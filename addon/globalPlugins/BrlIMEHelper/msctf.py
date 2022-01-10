# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2022 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import print_function
from __future__ import unicode_literals
from collections import OrderedDict
from comtypes import BSTR, CLSCTX_ALL, COMMETHOD, GUID, IUnknown
from comtypes.GUID import GUID_null
from comtypes.client import CreateObject
from ctypes import *
from ctypes.wintypes import *

REFCLSID = REFGUID = POINTER(GUID)
CLSID_TF_InputProcessorProfiles = GUID("{33C53A50-F456-4884-B049-85FD643ECFED}")
GUID_TFCAT_CATEGORY_OF_TIP = GUID("{534C48C1-0607-4098-A521-4FC899C73E90}")
GUID_TFCAT_DISPLAYATTRIBUTEPROVIDER = GUID("{046B8C80-1647-40F7-9B21-B93B81AABC1B}")
GUID_TFCAT_TIP_HANDWRITING = GUID("{246ECB87-C2F2-4ABE-905B-C8B38ADD2C43}")
GUID_TFCAT_TIP_KEYBOARD = GUID("{34745C63-B2F0-4784-8B67-5E12C8701A31}")
GUID_TFCAT_TIP_SPEECH = GUID("{B5A73CD1-8355-426B-A161-259808F26B14}")
GUID_TFCAT_TIPCAP_COMLESS = GUID("{364215D9-75BC-11D7-A6EF-00065B84435C}")
GUID_TFCAT_TIPCAP_SECUREMODE = GUID("{49D2F9CE-1F5E-11D7-A6D3-00065B84435C}")
GUID_TFCAT_TIPCAP_UIELEMENTENABLED = GUID("{49D2F9CF-1F5E-11D7-A6D3-00065B84435C}")
GUID_TFCAT_TIPCAP_WOW16 = GUID("{364215DA-75BC-11D7-A6EF-00065B84435C}")

def _IEnum_factory(etype, iid, method_order=None):
    class IEnumXXX(IUnknown):
        _iid_ = GUID(iid)
        def Next(self, celt):
            if celt == 0:
                return None
            elif celt < 0:
                raise ValueError("Negative number of elements is not allowed")
            array = (etype * celt)()
            celtFetched = self._Next(celt, array)
            if celtFetched <= 0:
                return None
            return array[0] if celt == 1 else array[:celtFetched]
    default_vtbl = OrderedDict([
        ("Next", COMMETHOD([], HRESULT, "Next",
            (["in"], ULONG, "celt"),
            (["in"], POINTER(etype), "rgelt"),
            (["out"], POINTER(ULONG), "pceltFetched")
        )),
        ("Skip", COMMETHOD([], HRESULT, "Skip",
            (["in"], ULONG, "celt")
        )),
        ("Reset", COMMETHOD([], HRESULT, "Reset")),
        ("Clone", COMMETHOD([], HRESULT, "Clone",
            (["out"], POINTER(POINTER(IEnumXXX)), "ppenum")
        )),
    ])
    IEnumXXX._methods_ = list(default_vtbl.values()) if method_order is None else [default_vtbl[m] for m in method_order]
    return IEnumXXX

class _Structure2str:
    def __init__(self):
        if not isinstance(self, Structure):
            raise TypeError("Inheritance from {0.__module__}.{0.__name__} is required".format(Structure))
    def __str__(self):
        return "{" + ", ".join("{0}: {1}".format(field[0], getattr(self, field[0])) for field in self._fields_) + "}"

class IEnumGUID(_IEnum_factory(GUID, "{0002E000-0000-0000-C000-000000000046}")):
    pass

class TF_LANGUAGEPROFILE(Structure, _Structure2str):
    _pack_ = 4
    _fields_ = [
        ("clsid", GUID),
        ("langid", LANGID),
        ("catid", GUID),
        ("fActive", BOOL),
        ("guidProfile", GUID),
    ]

class IEnumTfLanguageProfiles(_IEnum_factory(TF_LANGUAGEPROFILE, "{3D61BF11-AC5F-42C8-A4CB-931BCC28C744}", ("Clone", "Next", "Reset", "Skip"))):
    pass

class ITfInputProcessorProfiles(IUnknown):
    _iid_ = GUID("{1F02B6C5-7842-4EE6-8A0B-9A24183A95CA}")
    _methods_ = [
        COMMETHOD([], HRESULT, "Register",
            (["in"], REFCLSID, "rclsid"),
        ),
        COMMETHOD([], HRESULT, "Unregister",
            (["in"], REFCLSID, "rclsid"),
        ),
        COMMETHOD([], HRESULT, "AddLanguageProfile",
            (["in"], REFCLSID, "rclsid"),
            (["in"], LANGID, "langid"),
            (["in"], REFGUID, "guidProfile"),
            (["in"], c_wchar_p, "pchDesc"),
            (["in"], ULONG, "cchDesc"),
            (["in"], c_wchar_p, "pchIconFile"),
            (["in"], ULONG, "cchFile"),
            (["in"], ULONG, "uIconIndex"),
        ),
        COMMETHOD([], HRESULT, "RemoveLanguageProfile",
            (["in"], REFCLSID, "rclsid"),
            (["in"], LANGID, "langid"),
            (["in"], REFGUID, "guidProfile"),
        ),
        COMMETHOD([], HRESULT, "EnumInputProcessorInfo",
            (["out"], POINTER(POINTER(IEnumGUID)), "ppEnum"),
        ),
        COMMETHOD([], HRESULT, "GetDefaultLanguageProfile",
            (["in"], LANGID, "langid"),
            (["in"], REFGUID, "catid"),
            (["out"], POINTER(GUID), "pclsid"),
            (["out"], POINTER(GUID), "pguidProfile"),
        ),
        COMMETHOD([], HRESULT, "SetDefaultLanguageProfile",
            (["in"], LANGID, "langid"),
            (["in"], REFCLSID, "rclsid"),
            (["in"], REFGUID, "guidProfiles"),
        ),
        COMMETHOD([], HRESULT, "ActivateLanguageProfile",
            (["in"], REFCLSID, "rclsid"),
            (["in"], LANGID, "langid"),
            (["in"], REFGUID, "guidProfiles"),
        ),
        COMMETHOD([], HRESULT, "GetActiveLanguageProfile",
            (["in"], REFCLSID, "rclsid"),
            (["out"], POINTER(LANGID), "plangid"),
            (["out"], POINTER(GUID), "pguidProfile"),
        ),
        COMMETHOD([], HRESULT, "GetLanguageProfileDescription",
            (["in"], REFCLSID, "rclsid"),
            (["in"], LANGID, "langid"),
            (["in"], REFGUID, "guidProfile"),
            (["out"], POINTER(BSTR), "pbstrProfile"),
        ),
        COMMETHOD([], HRESULT, "GetCurrentLanguage",
            (["out"], POINTER(LANGID), "plangid"),
        ),
        COMMETHOD([], HRESULT, "ChangeCurrentLanguage",
            (["in"], LANGID, "langid"),
        ),
        COMMETHOD([], HRESULT, "GetLanguageList",
            (["out"], POINTER(POINTER(LANGID)), "pplangid"),
            (["out"], POINTER(ULONG), "pulCount"),
        ),
        COMMETHOD([], HRESULT, "EnumLanguageProfiles",
            (["in"], LANGID, "langid"),
            (["out"], POINTER(POINTER(IEnumTfLanguageProfiles)), "ppEnum"),
        ),
        COMMETHOD([], HRESULT, "EnableLanguageProfile",
            (["in"], REFCLSID, "rclsid"),
            (["in"], LANGID, "langid"),
            (["in"], REFGUID, "guidProfile"),
            (["in"], BOOL, "fEnable"),
        ),
        COMMETHOD([], HRESULT, "IsEnabledLanguageProfile",
            (["in"], REFCLSID, "rclsid"),
            (["in"], LANGID, "langid"),
            (["in"], REFGUID, "guidProfile"),
            (["out"], POINTER(BOOL), "pfEnable"),
        ),
        COMMETHOD([], HRESULT, "EnableLanguageProfileByDefault",
            (["in"], REFCLSID, "rclsid"),
            (["in"], LANGID, "langid"),
            (["in"], REFGUID, "guidProfile"),
            (["in"], BOOL, "fEnable"),
        ),
        COMMETHOD([], HRESULT, "SubstituteKeyboardLayout",
            (["in"], REFCLSID, "rclsid"),
            (["in"], LANGID, "langid"),
            (["in"], REFGUID, "guidProfile"),
            (["in"], HKL, "hKL"),
        ),
    ]
    def GetLanguageList(self):
        plangid, ulCount = self._GetLanguageList()
        rtn = plangid[:ulCount]
        oledll.ole32.CoTaskMemFree(plangid)
        return rtn
