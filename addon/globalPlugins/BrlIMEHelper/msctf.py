# -*- coding: UTF-8 -*-
# Copyright (C) 2019-2024 Bo-Cheng Jhan <school510587@yahoo.com.tw>
# This file is covered by the GNU General Public License.
# See the file LICENSE for more details.

from __future__ import print_function
from __future__ import unicode_literals
from collections import OrderedDict
from comtypes import BSTR, COMMETHOD, GUID, IUnknown
from comtypes.GUID import GUID_null
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
TF_CONVERSIONMODE_ALPHANUMERIC = 0
TF_CONVERSIONMODE_NATIVE = 0x0001
TF_CONVERSIONMODE_KATAKANA = 0x0002
TF_CONVERSIONMODE_FULLSHAPE = 0x0008
TF_CONVERSIONMODE_ROMAN = 0x0010
TF_CONVERSIONMODE_CHARCODE = 0x0020
TF_CONVERSIONMODE_SOFTKEYBOARD = 0x0080
TF_CONVERSIONMODE_NOCONVERSION = 0x0100
TF_CONVERSIONMODE_SYMBOL = 0x0400
TF_CONVERSIONMODE_FIXED = 0x0800
TF_PROFILETYPE_INPUTPROCESSOR = 1
TF_PROFILETYPE_KEYBOARDLAYOUT = 2

def _IEnum_factory(etype, iid, method_order=None):
    class IEnumXXX(IUnknown):
        _iid_ = GUID(iid)
        def Next(self, celt=None):
            if celt is None:
                array_length = 1
            else:
                array_length = int(celt)
                if array_length == 0:
                    return None
                elif array_length < 0:
                    raise ValueError("Negative number of elements is not allowed")
            array = (etype * array_length)()
            celtFetched = self._Next(array_length, array)
            if celtFetched <= 0:
                return None if celt is None else []
            return array[0] if celt is None else array[:celtFetched]
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

class TF_INPUTPROCESSORPROFILE(Structure, _Structure2str):
    _fields_ = [
        ("dwProfileType", DWORD),
        ("langid", LANGID),
        ("clsid", GUID),
        ("guidProfile", GUID),
        ("catid", GUID),
        ("hklSubstitute", HKL),
        ("dwCaps", DWORD),
        ("hkl", HKL),
        ("dwFlags", DWORD),
    ]

class IEnumTfInputProcessorProfiles(_IEnum_factory(TF_INPUTPROCESSORPROFILE, "{71C6E74D-0F28-11D8-A82A-00065B84435C}", ("Clone", "Next", "Reset", "Skip"))):
    pass

class ITfInputProcessorProfileMgr(IUnknown):
    _iid_ = GUID("{71C6E74C-0F28-11D8-A82A-00065B84435C}")
    _methods_ = [
        COMMETHOD([], HRESULT, "ActivateProfile",
            (["in"], DWORD, "dwProfileType"),
            (["in"], LANGID, "langid"),
            (["in"], REFCLSID, "clsid"),
            (["in"], REFGUID, "guidProfile"),
            (["in"], HKL, "hkl"),
            (["in"], DWORD, "dwFlags"),
        ),
        COMMETHOD([], HRESULT, "DeactivateProfile",
            (["in"], DWORD, "dwProfileType"),
            (["in"], LANGID, "langid"),
            (["in"], REFCLSID, "clsid"),
            (["in"], REFGUID, "guidProfile"),
            (["in"], HKL, "hkl"),
            (["in"], DWORD, "dwFlags"),
        ),
        COMMETHOD([], HRESULT, "GetProfile",
            (["in"], DWORD, "dwProfileType"),
            (["in"], LANGID, "langid"),
            (["in"], REFCLSID, "clsid"),
            (["in"], REFGUID, "guidProfile"),
            (["in"], HKL, "hkl"),
            (["out"], POINTER(TF_INPUTPROCESSORPROFILE), "pProfile"),
        ),
        COMMETHOD([], HRESULT, "EnumProfiles",
            (["in"], LANGID, "langid"),
            (["out"], POINTER(POINTER(IEnumTfInputProcessorProfiles)), "ppEnum"),
        ),
        COMMETHOD([], HRESULT, "ReleaseInputProcessor",
            (["in"], REFCLSID, "rclsid"),
            (["in"], DWORD, "dwFlags"),
        ),
        COMMETHOD([], HRESULT, "RegisterProfile",
            (["in"], REFCLSID, "rclsid"),
            (["in"], LANGID, "langid"),
            (["in"], REFGUID, "guidProfile"),
            (["in"], c_wchar_p, "pchDesc"),
            (["in"], ULONG, "cchDesc"),
            (["in"], c_wchar_p, "pchIconFile"),
            (["in"], ULONG, "cchFile"),
            (["in"], ULONG, "uIconIndex"),
            (["in"], HKL, "hklsubstitute"),
            (["in"], DWORD, "dwPreferredLayout"),
            (["in"], BOOL, "bEnabledByDefault"),
            (["in"], DWORD, "dwFlags"),
        ),
        COMMETHOD([], HRESULT, "UnregisterProfile",
            (["in"], REFCLSID, "rclsid"),
            (["in"], LANGID, "langid"),
            (["in"], REFGUID, "guidProfile"),
            (["in"], DWORD, "dwFlags"),
        ),
        COMMETHOD([], HRESULT, "GetActiveProfile",
            (["in"], REFGUID, "catid"),
            (["out"], POINTER(TF_INPUTPROCESSORPROFILE), "pProfile"),
        ),
    ]
    def _profile_spec(method):
        def wrapper(self, dwProfileType, *args, **kwargs):
            if isinstance(dwProfileType, TF_INPUTPROCESSORPROFILE):
                if len(args) > 0 or len(kwargs) > 1 or (len(kwargs) == 1 and "dwFlags" not in kwargs):
                    raise ArgumentError()
                profile = dwProfileType
            elif dwProfileType == TF_PROFILETYPE_INPUTPROCESSOR:
                try:
                    clsid = kwargs["clsid"]
                    if not isinstance(clsid, GUID):
                        kwargs["clsid"] = GUID(clsid)
                except (KeyError, NameError):
                    pass
                try:
                    guidProfile = kwargs["guidProfile"]
                    if isinstance(guidProfile, GUID):
                        kwargs["guidProfile"] = GUID(guidProfile)
                except (KeyError, NameError):
                    pass
                if "hkl" not in kwargs:
                    kwargs["hkl"] = 0
            elif dwProfileType == TF_PROFILETYPE_KEYBOARDLAYOUT:
                if kwargs.get("clsid") is None:
                    kwargs["clsid"] = GUID_null
                if kwargs.get("guidProfile") is None:
                    kwargs["guidProfile"] = GUID_null
            else:
                raise ValueError("Invalid profile type")
            return method(self, dwProfileType, *args, **kwargs)
        return wrapper
    @_profile_spec
    def ActivateProfile(self, dwProfileType, langid, clsid=None, guidProfile=None, hkl=0, dwFlags=0):
        return self._ActivateProfile(dwProfileType, langid, clsid, guidProfile, hkl, dwFlags)
    @_profile_spec
    def DeactivateProfile(self, dwProfileType, langid, clsid=None, guidProfile=None, hkl=0, dwFlags=0):
        return self._DeactivateProfile(dwProfileType, langid, clsid, guidProfile, hkl, dwFlags)
    @_profile_spec
    def GetProfile(self, dwProfileType, langid, clsid=None, guidProfile=None, hkl=0):
        return self._GetProfile(dwProfileType, langid, clsid, guidProfile, hkl)

if __name__ == "__main__":
    from comtypes import CLSCTX_ALL
    from comtypes.client import CreateObject
    oIPP = CreateObject(CLSID_TF_InputProcessorProfiles, CLSCTX_ALL, interface=ITfInputProcessorProfiles)
    for langid in oIPP.GetLanguageList():
        print("Language: %04X" % (langid,))
        gtr = oIPP.EnumLanguageProfiles(langid)
        while 1:
            profile = gtr.Next()
            if profile is None:
                break
            print("-+"[profile.fActive], end="")
            print(("DISABLED", "ENABLED")[oIPP.IsEnabledLanguageProfile(profile.clsid, langid, profile.guidProfile)], end="")
            print("", oIPP.GetLanguageProfileDescription(profile.clsid, langid, profile.guidProfile))
            print("  clsid:", profile.clsid)
            print("  guidProfile:", profile.guidProfile)
