import os
import wx

import psychopy
from psychopy.app.colorpicker import PsychoColorPicker
from psychopy.app.themes import ThemeMixin
from psychopy.colors import Color
from psychopy.localization import _translate
from psychopy import data, logging, prefs
import re


class _ValidatorMixin():
    def validate(self, evt):
        """Redirect validate calls to global validate method, assigning appropriate valType"""
        validate(self, self.valType)

    def showValid(self, valid):
        """Style input box according to valid"""
        if not hasattr(self, "SetForegroundColour"):
            return
        if valid:
            self.SetForegroundColour(wx.Colour(
                ThemeMixin.codeColors['base']['fg']
            ))
        else:
            self.SetForegroundColour(wx.Colour(
                1, 0, 0
            ))


BoolCtrl = wx.CheckBox


class ChoiceCtrl(wx.Choice, _ValidatorMixin):
    def __init__(self, parent, valType,
                 val="", choices=[], fieldName="",
                 size=wx.Size(-1, 24)):
        wx.Choice.__init__(self)
        self.Create(parent, -1, size=size, choices=choices, name=fieldName)
        self.valType = valType
        if val in choices:
            self.SetStringSelection(val)


class IntCtrl(wx.SpinCtrl, _ValidatorMixin):
    def __init__(self, parent, valType,
                 val="", fieldName="",
                 size=wx.Size(-1, 24)):
        wx.SpinCtrl.__init__(self)
        self.Create(parent, -1, str(val), name=fieldName, size=size)
        self.valType = valType
        self.Bind(wx.EVT_SPINCTRL, self.spin)

    def spin(self, evt):
        """Redirect validate calls to global validate method, assigning appropriate valType"""
        if evt.EventType == wx.EVT_SPIN_UP.evtType[0]:
            self.SetValue(str(int(self.GetValue())+1))
        elif evt.EventType == wx.EVT_SPIN_DOWN.evtType[0]:
            self.SetValue(str(int(self.GetValue()) - 1))
        validate(self, "int")


class CodeCtrl(wx.TextCtrl, _ValidatorMixin):
    def __init__(self, parent, valType,
                 val="", fieldName="",
                 size=wx.Size(-1, 24)):

        # Create self
        wx.TextCtrl.__init__(self)
        self.Create(parent, -1, val, name=fieldName, size=size)
        self.valType = valType
        # Add sizer
        self._szr = wx.BoxSizer(wx.HORIZONTAL)
        # Add $
        self.dollarLbl = wx.StaticText(parent, -1, "$", size=wx.Size(-1, -1), style=wx.ALIGN_RIGHT)
        self.dollarLbl.SetToolTipString(_translate("This parameter will be treated as code - we have already put in the $, so you don't have to."))
        self._szr.Add(self.dollarLbl, border=5, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.LEFT)
        # Add self to sizer
        self._szr.Add(self, border=5, flag=wx.EXPAND | wx.RIGHT)
        # Bind to validation
        self.Bind(wx.EVT_TEXT, self.validate)


class StringCtrl(wx.TextCtrl, _ValidatorMixin):
    def __init__(self, parent, valType,
                 val="", fieldName="",
                 size=wx.Size(-1, 24)):
        wx.TextCtrl.__init__(self)
        self.Create(parent, -1, val, name=fieldName, size=size)
        self.valType = valType
        self.Bind(wx.EVT_TEXT, self.codeWanted)

    def codeWanted(self, evt):
        if self.GetValue().startswith("$"):
            spec = ThemeMixin.codeColors.copy()
            base = spec['base']
            # Override base font with user spec if present
            if prefs.coder['codeFont'].lower() != "From Theme...".lower():
                base['font'] = prefs.coder['codeFont']
            validate(self, "code")
        else:
            validate(self, self.valType)


class ExtendedStringCtrl(StringCtrl, _ValidatorMixin):
    def __init__(self, parent, valType,
                 val="", fieldName="",
                 size=wx.Size(-1, 72)):
        StringCtrl.__init__(self, parent, val, fieldName, size)
        self.SetWindowStyleFlag(wx.TE_MULTILINE)


class ExtendedCodeCtrl(ExtendedStringCtrl, _ValidatorMixin):
    def codeWanted(self, evt):
        validate(self, "code")


class ColorCtrl(wx.TextCtrl, _ValidatorMixin):
    def __init__(self, parent, valType,
                 val="", fieldName="",
                 size=wx.Size(-1, 24)):
        # Create self
        wx.TextCtrl.__init__(self)
        self.Create(parent, -1, val, name=fieldName, size=size)
        self.valType = valType
        # Add sizer
        self._szr = wx.BoxSizer(wx.HORIZONTAL)
        self._szr.Add(self, border=5, flag=wx.EXPAND | wx.RIGHT)
        # Add button to activate color picker
        fldr = parent.app.iconCache.getBitmap(name="color", size=16, theme="light")
        self.pickerBtn = wx.BitmapButton(parent, -1, size=wx.Size(24,24), bitmap=fldr)
        self.pickerBtn.SetToolTip(_translate("Specify color ..."))
        self.pickerBtn.Bind(wx.EVT_BUTTON, self.colorPicker)
        self._szr.Add(self.pickerBtn)
        # Bind to validation
        self.Bind(wx.EVT_TEXT, self.validate)

    def colorPicker(self, evt):
        PsychoColorPicker(self.GetTopLevelParent().frame)


class TableCtrl(wx.TextCtrl, _ValidatorMixin):
    def __init__(self, parent, valType,
                 val="", fieldName="",
                 size=wx.Size(-1, 24)):
        # Create self
        wx.TextCtrl.__init__(self)
        self.Create(parent, -1, val, name=fieldName, size=size)
        self.valType = valType
        # Add sizer
        self._szr = wx.BoxSizer(wx.HORIZONTAL)
        self._szr.Add(self, border=5, flag=wx.EXPAND | wx.RIGHT)
        # Add button to browse for file
        fldr = parent.app.iconCache.getBitmap(name="folder", size=16, theme="light")
        self.findBtn = wx.BitmapButton(parent, -1, size=wx.Size(24,24), bitmap=fldr)
        self.findBtn.SetToolTip(_translate("Specify file ..."))
        self.findBtn.Bind(wx.EVT_BUTTON, self.findFile)
        self._szr.Add(self.findBtn)
        # Add button to open in Excel
        xl = parent.app.iconCache.getBitmap(name="filecsv", size=16, theme="light")
        self.xlBtn = wx.BitmapButton(parent, -1, size=wx.Size(24,24), bitmap=xl)
        self.xlBtn.SetToolTip(_translate("Open/create in your default table editor"))
        self.xlBtn.Bind(wx.EVT_BUTTON, self.openExcel)
        self._szr.Add(self.xlBtn)
        # Link to Excel templates for certain contexts
        cmpRoot = os.path.dirname(psychopy.experiment.components.__file__)
        self.templates = {
            'Form': os.path.join(cmpRoot, "form", "formItems.xltx")
        }
        # Configure validation
        self.Bind(wx.EVT_TEXT, self.validate)
        self.validExt = [".csv",".tsv",".txt",
                         ".xl",".xlsx",".xlsm",".xlsb",".xlam",".xltx",".xltm",".xls",".xlt",
                         ".htm",".html",".mht",".mhtml",
                         ".xml",".xla",".xlm",
                         ".odc",".ods",
                         ".udl",".dsn",".mdb",".mde",".accdb",".accde",".dbc",".dbf",
                         ".iqy",".dqy",".rqy",".oqy",
                         ".cub",".atom",".atomsvc",
                         ".prn",".slk",".dif"]
    def validate(self, evt):
        """Redirect validate calls to global validate method, assigning appropriate valType"""
        validate(self, "file")
        # Enable Excel button if valid
        self.xlBtn.Enable(self.valid)
        # Is component type available?
        if hasattr(self.GetTopLevelParent(), 'type'):
            # Does this component have a default template?
            if self.GetTopLevelParent().type in self.templates:
                self.xlBtn.Enable(True)

    def openExcel(self, event):
        """Either open the specified excel sheet, or make a new one from a template"""
        file = self.GetValue()
        if os.path.isfile(file) and file.endswith(tuple(self.validExt)):
            os.startfile(file)
        else:
            dlg = wx.MessageDialog(self, _translate(
                f"Once you have created and saved your table, please remember to add it to {self.Name}"),
                             caption="Reminder")
            dlg.ShowModal()
            os.startfile(self.templates[self.GetTopLevelParent().type])

    def findFile(self, event):
        _wld = f"All Table Files({'*'+';*'.join(self.validExt)})|{'*'+';*'.join(self.validExt)}|All Files (*.*)|*.*"
        dlg = wx.FileDialog(self, message=_translate("Specify file ..."),
                            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                            wildcard=_translate(_wld))
        if dlg.ShowModal() != wx.ID_OK:
            return 0
        filename = dlg.GetPath()
        relname = os.path.relpath(filename)
        self.SetValue(relname)
        self.validateInput(event)


class FileCtrl(wx.TextCtrl, _ValidatorMixin):
    def __init__(self, parent, valType,
                 val="", fieldName="",
                 size=wx.Size(-1, 24)):
        # Create self
        wx.TextCtrl.__init__(self)
        self.Create(parent, -1, val, name=fieldName, size=size)
        self.valType = valType
        # Add sizer
        self._szr = wx.BoxSizer(wx.HORIZONTAL)
        self._szr.Add(self, border=5, flag=wx.EXPAND | wx.RIGHT)
        # Add button to browse for file
        fldr = parent.app.iconCache.getBitmap(name="folder", size=16, theme="light")
        self.findBtn = wx.BitmapButton(parent, -1, size=wx.Size(24, 24), bitmap=fldr)
        self.findBtn.SetToolTip(_translate("Specify file ..."))
        self.findBtn.Bind(wx.EVT_BUTTON, self.findFile)
        self._szr.Add(self.findBtn)
        # Configure validation
        self.Bind(wx.EVT_TEXT, self.validate)

    def findFile(self, evt):
        _wld = f"All Files (*.*)|*.*"
        dlg = wx.FileDialog(self, message=_translate("Specify file ..."),
                            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                            wildcard=_translate(_wld))
        if dlg.ShowModal() != wx.ID_OK:
            return 0
        filename = dlg.GetPath()
        relname = os.path.relpath(filename)
        self.SetValue(relname)
        self.validate()


class FileListCtrl(wx.ListBox, _ValidatorMixin):
    def __init__(self, parent, valType,
                 choices=[], size=None, pathtype="rel"):
        wx.ListBox.__init__(self)
        self.valType = valType
        parent.Bind(wx.EVT_DROP_FILES, self.addItem)
        self.app = parent.app
        if type(choices) == str:
            choices = data.utils.listFromString(choices)
        self.Create(id=wx.ID_ANY, parent=parent, choices=choices, size=size, style=wx.LB_EXTENDED | wx.LB_HSCROLL)
        self.addBtn = wx.Button(parent, -1, style=wx.BU_EXACTFIT, label="+")
        self.addBtn.Bind(wx.EVT_BUTTON, self.addItem)
        self.subBtn = wx.Button(parent, -1, style=wx.BU_EXACTFIT, label="-")
        self.subBtn.Bind(wx.EVT_BUTTON, self.removeItem)

        self._szr = wx.BoxSizer(wx.HORIZONTAL)
        self.btns = wx.BoxSizer(wx.VERTICAL)
        self.btns.AddMany((self.addBtn, self.subBtn))
        self._szr.Add(self, proportion=1, flag=wx.EXPAND)
        self._szr.Add(self.btns)

    def addItem(self, event):
        if event.GetEventObject() == self.addBtn:
            _wld = "Any file (*.*)|*"
            dlg = wx.FileDialog(self, message=_translate("Specify file ..."),
                                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE,
                                wildcard=_translate(_wld))
            if dlg.ShowModal() != wx.ID_OK:
                return 0
            filenames = dlg.GetPaths()
            relname = []
            for filename in filenames:
                relname.append(
                    os.path.relpath(filename, self.GetTopLevelParent().frame.filename))
            self.InsertItems(relname, 0)
        else:
            fileList = event.GetFiles()
            for filename in fileList:
                if os.path.isfile(filename):
                    self.InsertItems(filename, 0)

    def removeItem(self, event):
        i = self.GetSelections()
        if isinstance(i, int):
            i = [i]
        items = [item for index, item in enumerate(self.Items)
                 if index not in i]
        self.SetItems(items)

    def GetValue(self):
        return self.Items

def validate(obj, valType):
    val = str(obj.GetValue())
    valid = True
    if val.startswith("$"):
        # If indicated as code, cancel and restart with different valType
        val = val[1:]
        valType = "code"
        return
    # Validate string
    if valType == "str":
        if re.findall(r"(?<!\\)\"", val):
            # If there are unescaped "
            valid = False
        if re.findall(r"(?<!\\)\'", val):
            # If there are unescaped '
            valid = False
    # Validate code
    if valType == "code":
        # For now, accept all code
        pass
    # Validate num
    if valType == "num":
        try:
            # Try to convert value to a float
            float(val)
        except ValueError:
            # If conversion fails, value is invalid
            valid = False
    # Validate int
    if valType == "int":
        try:
            # Try to convert value to int
            int(val)
        except ValueError:
            # If conversion fails, value is invalid
            valid = False
    # Validate list
    if valType == "list":
        empty = not bool(val) # Is value empty?
        fullList = re.fullmatch(r"[\(\[].*[\]\)]", val) # Is value full list with parentheses?
        partList = "," in val and not re.match(r"[\(\[].*[\]\)]", val) # Is value list without parentheses?
        singleVal = not " " in val or re.match(r"[\"\'].*[\"\']", val) # Is value a single value?
        if not any([empty, fullList, partList, singleVal]):
            # If value is not any of valid types, it is invalid
            valid = False
    # Validate color
    if valType == "color":
        # Strip function calls
        if re.fullmatch(r"\$?(Advanced)?Color\(.*\)", val):
            val = re.sub(r"\$?(Advanced)?Color\(", "", val[:-1])
        try:
            # Try to create a Color object from value
            obj.color = Color(val)
            if not obj.color:
                # If invalid object is created, input is invalid
                valid = False
        except:
            # If object creation fails, input is invalid
            valid = False
    if valType == "file":
        if not os.path.isfile(os.path.abspath(val)):
            # Is value a valid filepath?
            valid = False
        if hasattr(obj, "validExt"):
            if not val.endswith(tuple(obj.validExt)):
                # If control has specified list of ext, does value end in correct ext?
                valid = False

    # Apply valid status to object
    obj.valid = valid
    if hasattr(obj, "showValid"):
        obj.showValid(valid)