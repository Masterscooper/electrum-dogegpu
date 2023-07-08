import attr
import re
import hashlib

from enum import Enum, auto
from typing import Optional, Sequence, Mapping, Union, TYPE_CHECKING

from .bitcoin import address_to_script, construct_script, int_to_hex, opcodes, COIN, base_decode, base_encode, _op_push
from .i18n import _

from .transaction import PartialTxOutput, MalformedBitcoinScript, script_GetOp
from .json_db import StoredObject

from .util import ByteReader

# https://github.com/RavenProject/Ravencoin/blob/master/src/assets/assets.cpp

MAX_NAME_LENGTH = 32
MAX_CHANNEL_NAME_LENGTH = 12
MIN_ASSET_LENGTH = 3
MAX_VERIFIER_STING_LENGTH = 75

DEFAULT_ASSET_AMOUNT_MAX = 21_000_000_000
UNIQUE_ASSET_AMOUNT_MAX = 1
QUALIFIER_ASSET_AMOUNT_MAX = 10

RVN_ASSET_PREFIX = b'rvn'
RVN_ASSET_TYPE_CREATE = b'q'
RVN_ASSET_TYPE_CREATE_INT = RVN_ASSET_TYPE_CREATE[0]
RVN_ASSET_TYPE_OWNER = b'o'
RVN_ASSET_TYPE_OWNER_INT = RVN_ASSET_TYPE_OWNER[0]
RVN_ASSET_TYPE_TRANSFER = b't'
RVN_ASSET_TYPE_TRANSFER_INT = RVN_ASSET_TYPE_TRANSFER[0]
RVN_ASSET_TYPE_REISSUE = b'r'
RVN_ASSET_TYPE_REISSUE_INT = RVN_ASSET_TYPE_REISSUE[0]

ASSET_OWNER_IDENTIFIER = '!'

_ROOT_NAME_CHARACTERS = r'^[A-Z0-9._]{3,}$'
_SUB_NAME_CHARACTERS = r'^[A-Z0-9._]+$'
_UNIQUE_TAG_CHARACTERS = r'^[-A-Za-z0-9@$%&*()[\]{}_.?:]+$'
_MSG_CHANNEL_TAG_CHARACTERS = r'^[A-Za-z0-9_]+$'
_QUALIFIER_NAME_CHARACTERS = r'#[A-Z0-9._]{3,}$'
_SUB_QUALIFIER_NAME_CHARACTERS = r'#[A-Z0-9._]+$'
_RESTRICTED_NAME_CHARACTERS = r'\$[A-Z0-9._]{3,}$'

_DOUBLE_PUNCTUATION = r'^.*[._]{2,}.*$'
_LEADING_PUNCTUATION = r'^[._].*$'
_TRAILING_PUNCTUATION = r'^.*[._]$'
_QUALIFIER_LEADING_PUNCTUATION = r'^[#\$][._].*$'

_SUB_NAME_DELIMITER = '/'
_UNIQUE_TAG_DELIMITER = '#'
_MSG_CHANNEL_DELIMITER = '~'
_RESTRICTED_TAG_DELIMITER = '$'
_QUALIFIER_TAG_DELIMITER = '#'

_UNIQUE_INDICATOR = r'(^[^^~#!]+#[^~#!\/]+$)'
_MSG_CHANNEL_INDICATOR = r'(^[^^~#!]+~[^~#!\/]+$)'
_OWNER_INDICATOR = r'(^[^^~#!]+!$)'
_QUALIFIER_INDICATOR = r'^[#][A-Z0-9._]{3,}$'
_SUB_QUALIFIER_INDICATOR = r'^#[A-Z0-9._]+\/#[A-Z0-9._]+$'
_RESTRICTED_INDICATOR = r'^[\$][A-Z0-9._]{3,}$'

_BAD_NAMES = '^RVN$|^RAVEN$|^RAVENCOIN$|^RVNS$|^RAVENS$|^RAVENCOINS$|^#RVN$|^#RAVEN$|^#RAVENCOIN$|^#RVNS$|^#RAVENS$|^#RAVENCOINS$'

def _isMatchAny(symbol: str, badMatches: Sequence[str]) -> bool:
    return any((re.match(x, symbol) for x in badMatches))

def _isRootNameValid(symbol: str) -> bool:
    return re.match(_ROOT_NAME_CHARACTERS, symbol) and \
        not _isMatchAny(symbol, [_DOUBLE_PUNCTUATION, _LEADING_PUNCTUATION, _TRAILING_PUNCTUATION, _BAD_NAMES])

def _isQualifierNameValid(symbol: str) -> bool:
    return re.match(_QUALIFIER_NAME_CHARACTERS, symbol) and \
        not _isMatchAny(symbol, [_DOUBLE_PUNCTUATION, _QUALIFIER_LEADING_PUNCTUATION, _TRAILING_PUNCTUATION, _BAD_NAMES])

def _isRestrictedNameValid(symbol: str) -> bool:
    return re.match(_RESTRICTED_NAME_CHARACTERS, symbol) and \
        not _isMatchAny(symbol, [_DOUBLE_PUNCTUATION, _LEADING_PUNCTUATION, _TRAILING_PUNCTUATION, _BAD_NAMES])

def _isSubQualifierNameValid(symbol: str) -> bool:
    return re.match(_SUB_QUALIFIER_NAME_CHARACTERS, symbol) and \
        not _isMatchAny(symbol, [_DOUBLE_PUNCTUATION, _LEADING_PUNCTUATION, _TRAILING_PUNCTUATION])

def _isSubNameValid(symbol: str) -> bool:
    return re.match(_SUB_NAME_CHARACTERS, symbol) and \
        not _isMatchAny(symbol, [_DOUBLE_PUNCTUATION, _LEADING_PUNCTUATION, _TRAILING_PUNCTUATION])

def _isUniqueTagValid(symbol: str) -> bool:
    return re.match(_UNIQUE_TAG_CHARACTERS, symbol)

def _isMsgChannelTagValid(symbol: str) -> bool:
    return re.match(_MSG_CHANNEL_TAG_CHARACTERS, symbol) and \
        not _isMatchAny(symbol, [_DOUBLE_PUNCTUATION, _LEADING_PUNCTUATION, _TRAILING_PUNCTUATION])

def _isNameValidBeforeTag(symbol: str) -> bool:
    parts = symbol.split(_SUB_NAME_DELIMITER)
    for i, part in enumerate(parts):
        if i == 0:
            if not _isRootNameValid(part): return False
        else:
            if not _isSubNameValid(part): return False
    return True

def _isQualifierNameValidBeforeTag(symbol: str) -> bool:
    parts = symbol.split(_SUB_NAME_DELIMITER)
    if not _isQualifierNameValid(parts[0]): return False
    if len(parts) > 2: return False
    for part in parts[1:]:
        if not _isSubQualifierNameValid(part): return False

    return True

def _isAssetNameASubAsset(asset: str) -> bool:
    parts = asset.split(_SUB_NAME_DELIMITER)
    if not _isRootNameValid(parts[0]): return False
    return len(parts) > 1

def _isAssetNameASubQualifier(asset: str) -> bool:
    parts = asset.split(_SUB_NAME_DELIMITER)
    if not _isQualifierNameValid(parts[0]): return False
    return len(parts) > 1

class AssetType(Enum):
    ROOT = 1
    SUB = 2
    MSG_CHANNEL = 3
    OWNER = 4
    UNIQUE = 5
    QUALIFIER = 6
    SUB_QUALIFIER = 7
    RESTRICTED = 8

class AssetException(Exception):
    pass

def get_error_for_asset_typed(asset: str, asset_type: AssetType) -> Optional[str]:
    if asset_type == AssetType.SUB and _SUB_NAME_DELIMITER not in asset:
        return _('Not a sub asset.')
    if asset_type == AssetType.ROOT and _SUB_NAME_DELIMITER in asset:
        return _('Not a root asset.')
    if asset_type == AssetType.ROOT or asset_type == AssetType.SUB:
        if len(asset) > MAX_NAME_LENGTH - 1:
            return _('Name is greater than max length of {}.'.format(MAX_NAME_LENGTH - 1))
        
        if not _isAssetNameASubAsset(asset) and len(asset) < MIN_ASSET_LENGTH:
            return _('Name must contain at least {} characters.'.format(MIN_ASSET_LENGTH))

        valid = _isNameValidBeforeTag(asset)
        if not valid and _isAssetNameASubAsset(asset) and len(asset) < MIN_ASSET_LENGTH:
            return _('Name must have at least {} characters (Valid characters are: A-Z 0-9 _ .)'.format(MIN_ASSET_LENGTH))
        
        if not valid:
            return _('Name contains invalid characters (Valid characters are: A-Z 0-9 _ .) (special characters can\'t be the first or last characters)')

        return None
    else:
        if len(asset) > MAX_NAME_LENGTH:
            return _('Name is greater than max length of {}.'.format(MAX_NAME_LENGTH))

        if asset_type == AssetType.UNIQUE:
            parts = asset.split(_UNIQUE_TAG_DELIMITER)
            if len(parts) == 1:
                return _('Not a unique tag.')
            if not _isNameValidBeforeTag(parts[0]) or not _isUniqueTagValid(parts[-1]):
                return _('Unique name contains invalid characters (Valid characters are: A-Z a-z 0-9 @ $ % & * ( ) [ ] { } _ . ? : -)')
        elif asset_type == AssetType.MSG_CHANNEL:
            parts = asset.split(_MSG_CHANNEL_DELIMITER)
            if len(parts) == 1:
                return _('Not a message channel.')
            if len(parts[-1]) > MAX_CHANNEL_NAME_LENGTH:
                return _('Channel name is greater than max length of {}.'.format(MAX_CHANNEL_NAME_LENGTH))
            if not _isNameValidBeforeTag(parts[0]) or not _isMsgChannelTagValid(parts[-1]):
                return _('Message Channel name contains invalid characters (Valid characters are: A-Z 0-9 _ .) (special characters can\'t be the first or last characters)')
        elif asset_type == AssetType.OWNER:
            if not _isNameValidBeforeTag(asset[:-1]):
                return _('Owner name contains invalid characters (Valid characters are: A-Z 0-9 _ .) (special characters can\'t be the first or last characters)')
        elif asset_type == AssetType.QUALIFIER or asset_type == AssetType.SUB_QUALIFIER:
            if asset_type == AssetType.QUALIFIER:
                if _SUB_NAME_DELIMITER in asset:
                    return _('Not a qualifier')
            else:
                if _SUB_NAME_DELIMITER not in asset:
                    return _('Not a sub qualifier')
            if len(asset) < 4:
                return _('Name must contain at least {} characters.'.format(MIN_ASSET_LENGTH))
            if not _isQualifierNameValidBeforeTag(asset):
                return _('Qualifier name contains invalid characters (Valid characters are: A-Z 0-9 _ .) (# must be the first character, _ . special characters can\'t be the first or last characters)')
        elif asset_type == AssetType.RESTRICTED:
            if not _isRestrictedNameValid(asset):
                return _('Restricted name contains invalid characters (Valid characters are: A-Z 0-9 _ .) ($ must be the first character, _ . special characters can\'t be the first or last characters)')
        else:
            return _('Unknown asset type.')
        return None

def get_error_for_asset_name(asset: str) -> Optional[str]:
    if len(asset) > 40: return _('Asset is too long')

    if re.match(_UNIQUE_INDICATOR, asset): return get_error_for_asset_typed(asset, AssetType.UNIQUE)
    elif re.match(_MSG_CHANNEL_INDICATOR, asset): return get_error_for_asset_typed(asset, AssetType.MSG_CHANNEL)
    elif re.match(_OWNER_INDICATOR, asset): return get_error_for_asset_typed(asset, AssetType.OWNER)
    elif re.match(_QUALIFIER_INDICATOR, asset): return get_error_for_asset_typed(asset, AssetType.QUALIFIER)
    elif re.match(_SUB_QUALIFIER_INDICATOR, asset): return get_error_for_asset_typed(asset, AssetType.SUB_QUALIFIER)
    elif re.match(_RESTRICTED_INDICATOR, asset): return get_error_for_asset_typed(asset, AssetType.RESTRICTED)
    else: return get_error_for_asset_typed(asset, AssetType.SUB if _isAssetNameASubAsset(asset) else AssetType.ROOT)

def generate_create_script(address: str, asset: str, amount: int, divisions: int, reissuable: bool, associated_data: Optional[bytes]) -> 'str':
    if get_error_for_asset_name(asset):
        raise AssetException('Bad asset')
    if not amount > 0 or amount > DEFAULT_ASSET_AMOUNT_MAX * COIN:
        raise AssetException('Bad amount')
    if divisions < 0 or divisions > 8:
        raise AssetException('Bad divisions')
    if associated_data and len(associated_data) != 34:
        raise AssetException('Bad data')

    asset_data = (f'{RVN_ASSET_PREFIX.hex()}{RVN_ASSET_TYPE_CREATE.hex()}'
                  f'{int_to_hex(len(asset))}{asset.encode().hex()}'
                  f'{int_to_hex(amount, 8)}{int_to_hex(divisions)}'
                  f"{'01' if reissuable else '00'}{'01' if associated_data else '00'}"
                  f'{associated_data.hex() if associated_data else ""}')
    asset_script = construct_script([opcodes.OP_ASSET, asset_data, opcodes.OP_DROP])
    base_script = address_to_script(address)
    return base_script + asset_script

def generate_reissue_script(address: str, asset: str, amount: int, divisions: int, reissuable: bool, associated_data: Optional[bytes]) -> str:
    if get_error_for_asset_name(asset):
        raise AssetException('Bad asset')
    if not amount >= 0 or amount > DEFAULT_ASSET_AMOUNT_MAX * COIN:
        raise AssetException('Bad amount')
    if (divisions < 0 or divisions > 8) and divisions != 0xff:
        raise AssetException('Bad divisions')
    if associated_data and len(associated_data) != 34:
        raise AssetException('Bad data')

    asset_data = (f'{RVN_ASSET_PREFIX.hex()}{RVN_ASSET_TYPE_REISSUE.hex()}'
                  f'{int_to_hex(len(asset))}{asset.encode().hex()}'
                  f'{int_to_hex(amount, 8)}{int_to_hex(divisions)}'
                  f"{'01' if reissuable else '00'}"
                  f'{associated_data.hex() if associated_data else ""}')
    asset_script = construct_script([opcodes.OP_ASSET, asset_data, opcodes.OP_DROP])
    base_script = address_to_script(address)
    return base_script + asset_script

def generate_owner_script(address: str, asset: str) -> 'str':
    base_script = address_to_script(address)
    return generate_owner_script_from_base(asset, base_script)

def generate_owner_script_from_base(asset: str, base_script: str) -> 'str':
    if asset[-1] != ASSET_OWNER_IDENTIFIER:
        asset += ASSET_OWNER_IDENTIFIER
    if error := get_error_for_asset_name(asset):
        raise AssetException(f'Bad asset: {asset} {error}')
    
    asset_data = (f'{RVN_ASSET_PREFIX.hex()}{RVN_ASSET_TYPE_OWNER.hex()}'
                  f'{int_to_hex(len(asset))}{asset.encode().hex()}')
    
    asset_script = construct_script([opcodes.OP_ASSET, asset_data, opcodes.OP_DROP])
    return base_script + asset_script

def _asset_portion_of_transfer_script(asset: str, amount: int, *, memo: 'AssetMemo' = None) -> str:
    asset_data = (f'{RVN_ASSET_PREFIX.hex()}{RVN_ASSET_TYPE_TRANSFER.hex()}'
                  f'{int_to_hex(len(asset))}{asset.encode().hex()}'
                  f'{int_to_hex(amount, 8)}{memo.hex() if memo else ""}')
    asset_script = construct_script([opcodes.OP_ASSET, asset_data, opcodes.OP_DROP])
    return asset_script

def extra_size_for_asset_transfer(asset: str):
    return len(_asset_portion_of_transfer_script(asset, 0)) // 2

def generate_transfer_script_from_base(asset: str, amount: int, base_script: str):
    return base_script + _asset_portion_of_transfer_script(asset, amount)

def generate_verifier_tag(verifier_string: str) -> str:
    assert len(verifier_string) <= MAX_VERIFIER_STING_LENGTH
    asset_data = f'{int_to_hex(len(verifier_string))}{verifier_string.encode().hex()}'
    return construct_script([opcodes.OP_ASSET, opcodes.OP_RESERVED, asset_data])

def generate_null_tag(asset: str, h160: str, flag: bool) -> str:
    assert (error := get_error_for_asset_name(asset)) is None, error
    assert len(h160) == 40
    asset_data = f'{int_to_hex(len(asset))}{asset.encode().hex()}{"01" if flag else "00"}'
    return construct_script([opcodes.OP_ASSET, h160, asset_data])

def _associated_data_converter(input):
    if not input:
        return None
    if isinstance(input, str) and len(input) == 68:
        input = bytes.fromhex(input)
    if isinstance(input, bytes):
        if len(input) != 34:
            raise ValueError(f'{input=} is not 34 bytes')
        return input
    result = base_decode(input, base=58)
    if len(result) != 34:
        raise ValueError(f'{input=} decoded is not 34 bytes')
    return result


@attr.s
class AssetMemo:
    data = attr.ib(type=bytes, converter=_associated_data_converter)
    timestamp = attr.ib(default=None, type=int)

    def hex(self) -> str:
        return f'{self.data.hex()}{int_to_hex(self.timestamp, 8) if self.timestamp else ""}'

def _validate_sats(instance, attribute, value):
    if value <= 0:
        raise ValueError('sats must be greater than 0!')

def _validate_divisions(instance, attribute, value):
    if value < 0 or value > 8:
        raise ValueError('divisions must be 0-8!')

@attr.s
class AssetMetadata(StoredObject):
    sats_in_circulation = attr.ib(type=int, validator=_validate_sats)
    divisions = attr.ib(type=int, validator=_validate_divisions)
    reissuable = attr.ib(type=bool)
    associated_data = attr.ib(default=None, type=bytes, converter=_associated_data_converter)

    def associated_data_as_ipfs(self) -> Optional[str]:
        if not self.associated_data:
            return None
        return base_encode(self.associated_data, base=58)
    
    def status(self) -> Optional[str]:
        """ Returns the asset status as a hex string """
        h = ''.join([str(self.sats_in_circulation), 
                     str(self.divisions),
                     str(self.reissuable),
                     str(self.associated_data is not None)])
        if self.associated_data is not None:
            h += self.associated_data_as_ipfs()

        return hashlib.sha256(h.encode('ascii')).digest().hex()

class AssetVoutType(Enum):
    NONE = 1
    TRANSFER = 2
    CREATE = 3
    OWNER = 4
    REISSUE = 5

    NULL = 6
    VERIFIER = 7
    FREEZE = 8

class BaseAssetVoutInformation():
    asset = None
    amount: Optional[int] = None

    def __init__(self, type_: AssetVoutType, well_formed):
        self._type = type_
        self.well_formed_script = well_formed

    def get_type(self):
        return self._type
    
    def is_transferable(self):
        return self._type in (AssetVoutType.CREATE, AssetVoutType.OWNER, AssetVoutType.TRANSFER, AssetVoutType.REISSUE)

    def is_deterministic(self):
        return self._type in (AssetVoutType.TRANSFER, AssetVoutType.OWNER, AssetVoutType.NONE) and self.well_formed_script

    def is_tag(self):
        return False

class NoAssetVoutInformation(BaseAssetVoutInformation):
    def __init__(self):
        BaseAssetVoutInformation.__init__(self, AssetVoutType.NONE, True)

class MetadataAssetVoutInformation(BaseAssetVoutInformation):
    def __init__(self, type_: AssetVoutType, well_formed, asset: str, amount: int, divisions: int, reissuable: bool, associated_data: Optional[bytes]):
        BaseAssetVoutInformation.__init__(self, type_, well_formed)
        self.asset = asset
        self.amount = amount
        self.divisions = divisions
        self.reissuable = reissuable
        self.associated_data = associated_data

class OwnerAssetVoutInformation(BaseAssetVoutInformation):
    def __init__(self, well_formed, asset: str):
        BaseAssetVoutInformation.__init__(self, AssetVoutType.OWNER, well_formed)
        self.asset = asset
        self.amount = COIN

class TransferAssetVoutInformation(BaseAssetVoutInformation):
    def __init__(self, well_formed, asset: str, amount: int, asset_memo: Optional[bytes], asset_memo_timestamp: Optional[int]):
        BaseAssetVoutInformation.__init__(self, AssetVoutType.TRANSFER, well_formed)
        self.asset = asset
        self.amount = amount
        self.asset_memo = asset_memo
        self.asset_memo_timestamp = asset_memo_timestamp

    def is_deterministic(self):
        return self.asset_memo is None and self.asset_memo_timestamp is None and super().is_deterministic()

class TagAssetVoutInformation(BaseAssetVoutInformation):
    def is_deterministic(self):
        return True
    
    def is_tag(self):
        return True
    
class NullTagAssetVoutInformation(TagAssetVoutInformation):
    def __init__(self, asset: str, h160: str, flag: bool):
        BaseAssetVoutInformation.__init__(self, AssetVoutType.NULL, True)
        self.asset = asset
        self.h160 = h160
        self.flag = flag

class VerifierTagAssetVoutInformation(TagAssetVoutInformation):
    def __init__(self, verifier_string: str):
        BaseAssetVoutInformation.__init__(self, AssetVoutType.VERIFIER, True)
        self.verifier_string = verifier_string

class FreezeTagAssetVoutInformation(TagAssetVoutInformation):
    def __init__(self, asset: str, flag: bool):
        BaseAssetVoutInformation.__init__(self, AssetVoutType.FREEZE, True)
        self.asset = asset
        self.flag = flag

def get_asset_info_from_script(script: bytes) -> BaseAssetVoutInformation:
    try:
        decoded = [x for x in script_GetOp(script)]
    except MalformedBitcoinScript:
        return None

    try:
        for i, (op, _, index) in enumerate(decoded):
            if op == opcodes.OP_ASSET:
                asset_portion = script[index:]
                if i == 0:
                    if decoded[i + 1][0] == opcodes.OP_RESERVED:
                        if decoded[i + 2][0] == opcodes.OP_RESERVED:
                            internal_data = decoded[i + 3][1]
                            reader = ByteReader(internal_data)
                            asset_length = reader.read_byte_as_int()
                            asset_b = reader.read_bytes(asset_length)
                            flag = True if reader.read_byte_as_int() != 0 else False
                            return FreezeTagAssetVoutInformation(asset_b.decode(), flag)
                        else:
                            internal_data = decoded[i + 2][1]
                            verifier_string = next(script_GetOp(internal_data))[1]
                            return VerifierTagAssetVoutInformation(verifier_string.decode())
                    else:
                        reader = ByteReader(asset_portion)
                        first_byte = reader.read_byte_as_int()
                        if first_byte != 0x14: continue
                        h160 = reader.read_bytes(0x14)
                        internal_asset_portion_len = reader.read_byte_as_int()
                        asset_name_len = reader.read_byte_as_int()
                        asset_bytes = reader.read_bytes(asset_name_len)
                        flag = reader.read_byte_as_int()
                        return NullTagAssetVoutInformation(asset_bytes.decode(), h160.hex(), False if flag == 0 else True)
                else:
                    decoded_has_good_length = len(decoded) > i + 1
                    next_op_is_a_push = False
                    remaining_matches = False
                    if decoded_has_good_length:
                        next_op_is_a_push = decoded[i+1][1] is not None
                        if next_op_is_a_push:
                            op_push_prefix = bytes.fromhex(_op_push(len(decoded[i+1][1])))
                            remaining_matches = (op_push_prefix + decoded[i+1][1] + b'\x75') == asset_portion
                    well_formed = decoded_has_good_length and next_op_is_a_push and remaining_matches
                    
                    asset_prefix_position = asset_portion.find(RVN_ASSET_PREFIX)
                    if asset_prefix_position < 0: break
                    if len(asset_portion) < len(RVN_ASSET_PREFIX) + 3: break
                    reader = ByteReader(asset_portion[asset_prefix_position + len(RVN_ASSET_PREFIX):])
                    vout_type = reader.read_bytes(1)
                    if vout_type == RVN_ASSET_TYPE_CREATE:
                        asset_vout_type = AssetVoutType.CREATE
                    elif vout_type == RVN_ASSET_TYPE_OWNER:
                        asset_vout_type = AssetVoutType.OWNER
                    elif vout_type == RVN_ASSET_TYPE_TRANSFER:
                        asset_vout_type = AssetVoutType.TRANSFER
                    elif vout_type == RVN_ASSET_TYPE_REISSUE:
                        asset_vout_type = AssetVoutType.REISSUE
                    else: break

                    asset_length = reader.read_byte_as_int()
                    asset = reader.read_bytes(asset_length).decode()
                    if asset_vout_type == AssetVoutType.OWNER:
                        return OwnerAssetVoutInformation(well_formed, asset)

                    asset_amount_bytes = reader.read_bytes(8)
                    asset_amount = int.from_bytes(asset_amount_bytes, 'little')

                    if asset_vout_type == AssetVoutType.TRANSFER:
                        memo = None
                        timestamp = None
                        if reader.can_read_amount(34):
                            memo = reader.read_bytes(34)
                            if reader.can_read_amount(8):
                                timestamp_bytes = reader.read_bytes(8)
                                timestamp = int.from_bytes(timestamp_bytes, 'little')
                        return TransferAssetVoutInformation(well_formed, asset, asset_amount, memo, timestamp)
                    
                    divisions = reader.read_byte_as_int()
                    reissuable = reader.read_byte_as_int() == 1

                    if asset_vout_type == AssetVoutType.CREATE:
                        has_associated_data = reader.read_byte_as_int() == 1
                        if has_associated_data:
                            associated_data = reader.read_bytes(34)
                            return MetadataAssetVoutInformation(asset_vout_type, well_formed, asset, asset_amount, divisions, reissuable, associated_data)
                        else:
                            return MetadataAssetVoutInformation(asset_vout_type, well_formed, asset, asset_amount, divisions, reissuable, None)
                    elif asset_vout_type == AssetVoutType.REISSUE:
                        if reader.can_read_amount(34):
                            associated_data = reader.read_bytes(34)
                            return MetadataAssetVoutInformation(asset_vout_type, well_formed, asset, asset_amount, divisions, reissuable, associated_data)
                        else:
                            return MetadataAssetVoutInformation(asset_vout_type, well_formed, asset, asset_amount, divisions, reissuable, None)
                    break
    except IndexError:
        pass
    return NoAssetVoutInformation()

'''
The order of operations for Boolean algebra, from highest to lowest priority is NOT, then AND, then OR. 
Expressions inside brackets are always evaluated first.
'''

class BooleanExprAST:

    class OP(Enum):
        NONE = auto()
        AND = auto()
        OR = auto()
        NOT = auto()
        VAR = auto()

    def __init__(self, op, *, error: str = None):
        self.l_chld = None
        self.r_chld = None
        self.op = op
        self._error = error

    def error(self) -> Optional[str]:
        if self._error is not None: return self._error
        if self.op == self.OP.VAR: return None
        if self.l_chld is not None:
            if error := self.l_chld.error(): return error
        if self.r_chld is not None:
            if error := self.r_chld.error(): return error
        return None

    def iterate_vars_return_first(self, callable) -> Optional[str]:
        if self.op == self.OP.VAR:
            return callable(self.l_chld)
        if self.l_chld is not None:
            if ret := self.l_chld.iterate_vars_return_first(callable): return ret
        if self.r_chld is not None:
            if ret := self.r_chld.iterate_vars_return_first(callable): return ret
        return None

    def __repr__(self):
        return f'({self.op} [{self.l_chld},{self.r_chld}], {self._error=})'

    def evaluate(self, bool_dict):
        if self._error:
            raise Exception(self._error)

        if self.op == self.OP.AND:
            assert isinstance(self.l_chld, BooleanExprAST)
            assert isinstance(self.r_chld, BooleanExprAST)
            return self.l_chld.evaluate(bool_dict) and self.r_chld.evaluate(bool_dict)
        elif self.op == self.OP.OR:
            assert isinstance(self.l_chld, BooleanExprAST)
            assert isinstance(self.r_chld, BooleanExprAST)
            return self.l_chld.evaluate(bool_dict) or self.r_chld.evaluate(bool_dict)
        elif self.op == self.OP.NOT:
            assert isinstance(self.l_chld, BooleanExprAST)
            assert self.r_chld is None
            return not self.l_chld.evaluate(bool_dict)
        elif self.op == self.OP.VAR:
            assert isinstance(self.l_chld, str)
            assert self.r_chld is None
            value = bool_dict.get(self.l_chld, None)
            if value is None:
                raise Exception(f'Key {self.l_chld} does not exist')
            return value
        else:
            raise Exception(f'Unknown OP {self.op}')

    @classmethod
    def parse_string(cls, verifier) -> 'BooleanExprAST':
        if len(verifier) == 0:
            return cls(cls.OP.NONE, error=_('Empty string'))
        if len(verifier) > 80:
            return cls(cls.OP.NONE, error=_('Verifier is too long'))

        last_parenthesis_index = None
        last_name_index = None
        l_tok = 0
        r_tok = 0
        top_level_parenthesized = []
        # Transform parenthesis and variables to nodes at the top level
        for i, ch in enumerate(verifier):
            if last_parenthesis_index is None:
                if re.match(r'^[A-Z0-9._]$', ch):
                    if last_name_index is None:
                        last_name_index = i
                    continue
                else:
                    if last_name_index is not None:
                        node = cls(cls.OP.VAR)
                        node.l_chld = verifier[last_name_index:i]
                        top_level_parenthesized.append(node)
                        last_name_index = None

            if ch == '(':
                if l_tok == 0:
                    last_parenthesis_index = i
                l_tok += 1
            elif ch == ')':
                r_tok += 1

            if l_tok == r_tok and last_parenthesis_index is not None:
                top_level_parenthesized.append(
                cls.parse_string(verifier[last_parenthesis_index + 1:i]))
                l_tok = 0
                r_tok = 0
                last_parenthesis_index = None
                continue

            if last_parenthesis_index is not None: continue

            if ch in ('&', '|', '!'):
                top_level_parenthesized.append(ch)
            else:
                return cls(cls.OP.NONE, error=_(f'Unable to parse token {ch}'))

        if re.match(r'^[A-Z0-9._]$', ch) and last_name_index is not None:
            node = cls(cls.OP.VAR)
            node.l_chld = verifier[last_name_index:i + 1]
            top_level_parenthesized.append(node)

        is_not = False
        all_nots_resolved = True
        top_level_p_n = []
        for item in top_level_parenthesized:
            if item == '!':
                all_nots_resolved = False
                is_not = not is_not
            else:
                all_nots_resolved = True
                if is_not:
                    is_not = False
                    node = cls(cls.OP.NOT)
                    node.l_chld = item
                    top_level_p_n.append(node)
                else:
                    top_level_p_n.append(item)

        if not all_nots_resolved:
            return cls(cls.OP.NONE, error=_('Bad NOT placement'))

        looking_for_right_side_of_and = False
        top_level_p_n_a = []
        for item in top_level_p_n:
            if item == '&':
                looking_for_right_side_of_and = True
            else:
                if looking_for_right_side_of_and:
                    if len(top_level_p_n_a) == 0:
                        return cls(cls.OP.NONE, error=_('No left side of AND statement'))
                    else:
                        item_l = top_level_p_n_a.pop()
                        node = cls(cls.OP.AND)
                        node.l_chld = item_l
                        node.r_chld = item
                        top_level_p_n_a.append(node)
                else:
                    top_level_p_n_a.append(item)
                looking_for_right_side_of_and = False

        if looking_for_right_side_of_and:
            return cls(cls.OP.NONE, error=_('No right side of AND statement'))

        looking_for_right_side_of_or = False
        top_level_p_n_a_o = []
        for item in top_level_p_n_a:
            if item == '|':
                looking_for_right_side_of_or = True
            else:
                if looking_for_right_side_of_or:
                    if len(top_level_p_n_a_o) == 0:
                        return cls(cls.OP.NONE, error=_('No left side of OR statement'))
                    else:
                        item_l = top_level_p_n_a_o.pop()
                        node = cls(cls.OP.OR)
                        node.l_chld = item_l
                        node.r_chld = item
                        top_level_p_n_a_o.append(node)
                else:
                    top_level_p_n_a_o.append(item)
                looking_for_right_side_of_or = False

        if looking_for_right_side_of_or:
            return cls(cls.OP.NONE, error=_('No right side of OR statement'))
        if len(top_level_p_n_a_o) > 1:
            return cls(cls.OP.NONE,
                    error=_('Variables exist with no operators between them'))
        return top_level_p_n_a_o[0]

def compress_verifier_string(verifier: str) -> str:
    return verifier.replace(' ', '').replace(_QUALIFIER_TAG_DELIMITER, '')

def parse_verifier_string(verifier: str) -> BooleanExprAST:
    return BooleanExprAST.parse_string(compress_verifier_string(verifier))
