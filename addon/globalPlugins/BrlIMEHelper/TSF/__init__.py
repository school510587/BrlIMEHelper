from __future__ import print_function
from __future__ import unicode_literals
from comtypes import BSTR, CLSCTX_ALL, COMMETHOD, GUID, IUnknown
from comtypes.GUID import GUID_null
from comtypes.client import CreateObject
from ctypes import *
from ctypes.wintypes import *

from .constants import *

# WM_INPUTLANGCHANGEREQUEST = 0x0050
REFCLSID = REFGUID = POINTER(GUID)

def IEnum_factory(etype, iid, method_order=None):
    class IEnumXXX(IUnknown):
        _iid_ = GUID(iid)
        def __iter__(self):
            return self
        def __next__(self):
            item = self.Next(1)
            if item is None:
                raise StopIteration
            return item
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
    from collections import OrderedDict
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

class Structure2str:
    def __init__(self):
        if not isinstance(self, Structure):
            raise TypeError("Inheritance from {0.__module__}.{0.__name__} is required".format(Structure))
    def __str__(self):
        return "{" + ", ".join("{0}: {1}".format(field[0], getattr(self, field[0])) for field in self._fields_) + "}"

class IEnumGUID(IEnum_factory(GUID, "{0002E000-0000-0000-C000-000000000046}")):
    pass

class TF_LANGUAGEPROFILE(Structure, Structure2str):
    _pack_ = 4
    _fields_ = [
        ("clsid", GUID),
        ("langid", LANGID),
        ("catid", GUID),
        ("fActive", BOOL),
        ("guidProfile", GUID),
    ]

class IEnumTfLanguageProfiles(IEnum_factory(TF_LANGUAGEPROFILE, "{3D61BF11-AC5F-42C8-A4CB-931BCC28C744}", ("Clone", "Next", "Reset", "Skip"))):
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

class TF_INPUTPROCESSORPROFILE(Structure, Structure2str):
    _pack_ = 4
    _fields_ = [
        ("dwProfileType;", DWORD),
        ("langid", LANGID),
        ("clsid", GUID),
        ("guidProfile", GUID),
        ("catid", GUID),
        ("hklSubstitute", HKL),
        ("dwCaps", DWORD),
        ("hkl", HKL),
        ("dwFlags", DWORD),
    ]

class IEnumTfInputProcessorProfiles(IEnum_factory(TF_INPUTPROCESSORPROFILE, "{71C6E74D-0F28-11D8-A82A-00065B84435C}", ("Clone", "Next", "Reset", "Skip"))):
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
            if dwProfileType == TF_PROFILETYPE_INPUTPROCESSOR:
                try:
                    clsid = kwargs["clsid"]
                    if isinstance(clsid, GUID):
                        kwargs["clsid"] = byref(clsid)
                    elif isinstance(clsid, str) or isinstance(clsid, unicode):
                        clsid = GUID(clsid)
                        kwargs["clsid"] = byref(clsid)
                except (KeyError, NameError):
                    pass
                try:
                    guidProfile = kwargs["guidProfile"]
                    if isinstance(guidProfile, GUID):
                        kwargs["guidProfile"] = byref(guidProfile)
                    elif isinstance(guidProfile, str) or isinstance(guidProfile, unicode):
                        guidProfile = GUID(guidProfile)
                        kwargs["guidProfile"] = byref(guidProfile)
                except (KeyError, NameError):
                    pass
                if "hkl" not in kwargs:
                    kwargs["hkl"] = 0
            elif dwProfileType == TF_PROFILETYPE_KEYBOARDLAYOUT:
                if kwargs.get("clsid") is None:
                    clsid = GUID_null
                    kwargs["clsid"] = byref(clsid)
                if kwargs.get("guidProfile") is None:
                    guidProfile = GUID_null
                    kwargs["guidProfile"] = byref(guidProfile)
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
