# -*- coding: utf-8 -*-
#
# Electrum - lightweight Bitcoin client
# Copyright (C) 2018 The Electrum developers
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import json

from typing import NamedTuple, Union

# Can't import from util due to circular
def inv_dict(d):
    return {v: k for k, v in d.items()}

def read_json(filename, default):
    path = os.path.join(os.path.dirname(__file__), filename)
    try:
        with open(path, 'r') as f:
            r = json.loads(f.read())
    except:
        r = default
    return r


GIT_REPO_URL = "https://github.com/Masterscooper/electrum-dogegpu"
GIT_REPO_ISSUES_URL = "https://github.com/Masterscooper/electrum-dogegpu/issues"
BIP39_WALLET_FORMATS = read_json('bip39_wallet_formats.json', [])


class BurnAmounts(NamedTuple):
    IssueAssetBurnAmount: Union[int, float]
    ReissueAssetBurnAmount: Union[int, float]
    IssueSubAssetBurnAmount: Union[int, float]
    IssueUniqueAssetBurnAmount: Union[int, float]
    IssueMsgChannelAssetBurnAmount: Union[int, float]
    IssueQualifierAssetBurnAmount: Union[int, float]
    IssueSubQualifierAssetBurnAmount: Union[int, float]
    IssueRestrictedAssetBurnAmount: Union[int, float]
    AddNullQualifierTagBurnAmount: Union[int, float]


class BurnAddresses(NamedTuple):
    IssueAssetBurnAddress: str
    ReissueAssetBurnAddress: str
    IssueSubAssetBurnAddress: str
    IssueUniqueAssetBurnAddress: str
    IssueMsgChannelAssetBurnAddress: str
    IssueQualifierAssetBurnAddress: str
    IssueSubQualifierAssetBurnAddress: str
    IssueRestrictedAssetBurnAddress: str
    AddNullQualifierTagBurnAddress: str
    GlobalBurnAddress: str

class AbstractNet:
    GENESIS = None
    CHECKPOINTS = None
    DGW_CHECKPOINTS = None
    DGW_CHECKPOINTS_SPACING = 0
    DGW_CHECKPOINTS_START = 0
    MATURE = 0

    NET_NAME: str
    TESTNET: bool
    WIF_PREFIX: int
    ADDRTYPE_P2PKH: int
    ADDRTYPE_P2SH: int
    SEGWIT_HRP: str
    BOLT11_HRP: str
    GENESIS: str
    BLOCK_HEIGHT_FIRST_LIGHTNING_CHANNELS: int = 0
    BIP44_COIN_TYPE: int
    LN_REALM_BYTE: int

    @classmethod
    def max_legacy_checkpoint(cls) -> int:
        return max(0, len(cls.CHECKPOINTS) * 2016 - 1)

    @classmethod
    def max_checkpoint(cls) -> int:
        # DGW Checkpoints start at height 1 and are every 2016 blocks after
        return max(0, cls.DGW_CHECKPOINTS_START + (len(cls.DGW_CHECKPOINTS) * cls.DGW_CHECKPOINTS_SPACING) - 1)

    @classmethod
    def rev_genesis_bytes(cls) -> bytes:
        from . import bitcoin
        return bytes.fromhex(bitcoin.rev_hex(cls.GENESIS))


class DogeGPUMainnet(AbstractNet):
    NET_NAME = "mainnet"
    TESTNET = False
    WIF_PREFIX = 128
    ADDRTYPE_P2PKH = 38
    ADDRTYPE_P2SH = 98
    ADDRTYPE_P2SH_ALT = 98
    MATURE = 60
    SEGWIT_HRP = "dp"
    BOLT11_HRP = SEGWIT_HRP
    GENESIS = "00000052129a4a8d7f095769951e24a0b6f82a68670324985d7733ec4686d3b4"
    DEFAULT_PORTS = {'t': '50001', 's': '50002'}
    DEFAULT_SERVERS = read_json('servers.json', {})
    CHECKPOINTS = []
    DGW_CHECKPOINTS = read_json('checkpoints_dgw.json', [])
    DGW_CHECKPOINTS_SPACING = 2016
    DGW_CHECKPOINTS_START = 0 

    X16Rv2ActivationTS = 0
    KawpowActivationTS = 1711951200
    KawpowActivationHeight = 1
    nDGWActivationBlock = 1

    DEFAULT_MESSAGE_CHANNELS = ['ELECTRUM_DOGEGPU~notification']
    ASSET_PREFIX = b'dogpu'
    SHORT_NAME = 'DOGPU'
    LONG_NAME = 'DogeGPU'

    MULTISIG_ASSETS = False

    XPRV_HEADERS = {
        'standard': 0x0488ade4,  # xprv
        'p2wpkh-p2sh': 0x049d7878,  # yprv
        'p2wsh-p2sh': 0x0295b005,  # Yprv
        'p2wpkh': 0x04b2430c,  # zprv
        'p2wsh': 0x02aa7a99,  # Zprv
    }
    XPRV_HEADERS_INV = inv_dict(XPRV_HEADERS)
    XPUB_HEADERS = {
        'standard': 0x0488b21e,  # xpub
        'p2wpkh-p2sh': 0x049d7cb2,  # ypub
        'p2wsh-p2sh': 0x0295b43f,  # Ypub
        'p2wpkh': 0x04b24746,  # zpub
        'p2wsh': 0x02aa7ed3,  # Zpub
    }
    XPUB_HEADERS_INV = inv_dict(XPUB_HEADERS)
    BIP44_COIN_TYPE = 175

    BURN_AMOUNTS = BurnAmounts(
        IssueAssetBurnAmount=50000,
        ReissueAssetBurnAmount=10000,
        IssueSubAssetBurnAmount=10000,
        IssueUniqueAssetBurnAmount=500,
        IssueMsgChannelAssetBurnAmount=10000,
        IssueQualifierAssetBurnAmount=100000,
        IssueSubQualifierAssetBurnAmount=10000,
        IssueRestrictedAssetBurnAmount=150000,
        AddNullQualifierTagBurnAmount=0.1
    )

    BURN_ADDRESSES = BurnAddresses(
        IssueAssetBurnAddress='GXissueAssetXXXXXXXXXXXXXXXXY4EpkH',
        ReissueAssetBurnAddress='GXReissueAssetXXXXXXXXXXXXXXUDgdkK',
        IssueSubAssetBurnAddress='GXissueSubAssetXXXXXXXXXXXXXa34vJz',
        IssueUniqueAssetBurnAddress='GXissueUniqueAssetXXXXXXXXXXU8Wezq',
        IssueMsgChannelAssetBurnAddress='GXissueMsgChanneLAssetXXXXXXXXxtR5',
        IssueQualifierAssetBurnAddress='GXissueQuaLifierXXXXXXXXXXXXU4k5t4',
        IssueSubQualifierAssetBurnAddress='GXissueSubQuaLifierXXXXXXXXXZ6ha2f',
        IssueRestrictedAssetBurnAddress='GXissueRestrictedXXXXXXXXXXXY1gTsx',
        AddNullQualifierTagBurnAddress='GXaddTagBurnXXXXXXXXXXXXXXXXV6kAW2',
        GlobalBurnAddress='GXBurnXXXXXXXXXXXXXXXXXXXXXXWVNjr8'
    )


class DogeGPUTestnet(AbstractNet):
    NET_NAME = "testnet"
    BIP44_COIN_TYPE = 1
    LN_REALM_BYTE = 0
    LN_DNS_SEEDS = [
    ]
    TESTNET = True
    WIF_PREFIX = 239
    ADDRTYPE_P2PKH = 111
    ADDRTYPE_P2SH = 196
    ADDRTYPE_P2SH_ALT = 196
    MATURE = 60
    SEGWIT_HRP = "tc"
    BOLT11_HRP = SEGWIT_HRP
    GENESIS = "000000ecfc5e6324a079542221d00e10362bdc894d56500c414060eea8a3ad5a"
    DEFAULT_PORTS = {'t': '51001', 's': '51002'}
    DEFAULT_SERVERS = read_json('servers_testnet.json', {})
    CHECKPOINTS = []
    DGW_CHECKPOINTS = read_json('checkpoints_dgw_testnet.json', [])
    DGW_CHECKPOINTS_SPACING = 2016
    DGW_CHECKPOINTS_START = 0

    X16Rv2ActivationTS = 1567533600
    KawpowActivationTS = 1585159200
    KawpowActivationHeight = 231544
    nDGWActivationBlock = 1

    DEFAULT_MESSAGE_CHANNELS = []
    ASSET_PREFIX = b'dogpu'
    SHORT_NAME = 'tDOGPU'
    LONG_NAME = 'DogeGPU'
    MULTISIG_ASSETS = False
    
    XPRV_HEADERS = {
        'standard': 0x04358394,  # tprv
        'p2wpkh-p2sh': 0x044a4e28,  # uprv
        'p2wsh-p2sh': 0x024285b5,  # Uprv
        'p2wpkh': 0x045f18bc,  # vprv
        'p2wsh': 0x02575048,  # Vprv
    }
    XPRV_HEADERS_INV = inv_dict(XPRV_HEADERS)
    XPUB_HEADERS = {
        'standard': 0x043587cf,  # tpub
        'p2wpkh-p2sh': 0x044a5262,  # upub
        'p2wsh-p2sh': 0x024289ef,  # Upub
        'p2wpkh': 0x045f1cf6,  # vpub
        'p2wsh': 0x02575483,  # Vpub
    }
    XPUB_HEADERS_INV = inv_dict(XPUB_HEADERS)

    BURN_AMOUNTS = BurnAmounts(
        IssueAssetBurnAmount=500,
        ReissueAssetBurnAmount=100,
        IssueSubAssetBurnAmount=100,
        IssueUniqueAssetBurnAmount=5,
        IssueMsgChannelAssetBurnAmount=100,
        IssueQualifierAssetBurnAmount=1000,
        IssueSubQualifierAssetBurnAmount=100,
        IssueRestrictedAssetBurnAmount=1500,
        AddNullQualifierTagBurnAmount=0.1
    )

    BURN_ADDRESSES = BurnAddresses(
        IssueAssetBurnAddress='n1issueAssetXXXXXXXXXXXXXXXXWdnemQ',
        ReissueAssetBurnAddress='n1ReissueAssetXXXXXXXXXXXXXXWG9NLd',
        IssueSubAssetBurnAddress='n1issueSubAssetXXXXXXXXXXXXXbNiH6v',
        IssueUniqueAssetBurnAddress='n1issueUniqueAssetXXXXXXXXXXS4695i',
        IssueMsgChannelAssetBurnAddress='n1issueMsgChanneLAssetXXXXXXT2PBdD',
        IssueQualifierAssetBurnAddress='n1issueQuaLifierXXXXXXXXXXXXUysLTj',
        IssueSubQualifierAssetBurnAddress='n1issueSubQuaLifierXXXXXXXXXYffPLh',
        IssueRestrictedAssetBurnAddress='n1issueRestrictedXXXXXXXXXXXXZVT9V',
        AddNullQualifierTagBurnAddress='n1addTagBurnXXXXXXXXXXXXXXXXX5oLMH',
        GlobalBurnAddress='n1BurnXXXXXXXXXXXXXXXXXXXXXXU1qejP'
    )


def all_subclasses(cls):
    """Return all (transitive) subclasses of cls."""
    res = set(cls.__subclasses__())
    for sub in res.copy():
        res |= all_subclasses(sub)
    return res

NETS_LIST = tuple(all_subclasses(AbstractNet))

# don't import net directly, import the module instead (so that net is singleton)
net = DogeGPUMainnet


def set_mainnet():
    global net
    net = DogeGPUMainnet

def set_testnet():
    global net
    net = DogeGPUTestnet
