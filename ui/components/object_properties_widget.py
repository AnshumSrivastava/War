"""
FILE: ui/components/object_properties_widget.py
ROLE: The "Inspector" (Properties & Hierarchy).

DESCRIPTION:
This file creates the "Layers" panel you see on the left or right side of the screen.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout, QLineEdit, QSpinBox, QComboBox, QSlider, QFrame, QProgressBar, QToolButton, QSizePolicy, QScrollArea, QPushButton)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from engine.state.global_state import GlobalState
from ui.styles.theme import Theme

# --- UI CONFIGURATION ---
# Titles & Headers
STR_TITLE_INSPECTOR = "OBJECT INSPECTOR"
STR_TITLE_PROPERTIES = "PROPERTIES"
STR_TITLE_WORLD_EDITOR = "WORLD EDITOR"
STR_TITLE_SCENARIO_SETUP = "SCENARIO SETUP"
STR_TITLE_HEX_FMT = "HEX {coords}"

# Group Headers
STR_GRP_TERRAIN = "Terrain Data"
STR_GRP_DIMENSIONS = "Map Dimensions"
STR_GRP_IDENTITY = "Identity"
STR_GRP_COMMAND = "Command"
STR_GRP_VITALS = "Vitals"
STR_GRP_CONFIG = "Configuration"

# Labels
STR_LBL_TYPE = "Type"
STR_LBL_ELEVATION = "Elevation"
STR_LBL_WIDTH = "Width"
STR_LBL_HEIGHT = "Height"
STR_LBL_NAME = "Name"
STR_LBL_AGENT_TYPE = "Agent Type"
STR_LBL_AFFILIATION = "Affiliation"
STR_LBL_HIERARCHY = "Hierarchy"
STR_LBL_PERSONNEL = "Personnel"
STR_LBL_ZONE_NAME = "Zone Name"
STR_LBL_AURA_COLOR = "Aura Color"
STR_LBL_PATH_NAME = "Path Name"
STR_LBL_VECTOR_COLOR = "Vector Color"

# Tips & Instructional Text
STR_TIP_TERRAIN = "Select a hex to modify its terrain properties. Use the left toolbar for painting tools."
STR_TIP_SCENARIO = "Deploy agents and define strategic zones. Change side filtering via the top tabs."
STR_TIP_DEFAULT = "Select an object to view and edit its properties."

# Button Texts
STR_BTN_DELETE = "Delete Object"

# Data Lists
LIST_TERRAIN_TYPES = ["plains", "forest", "water", "mountain", "urban"]
LIST_SIDES = ["Attacker", "Defender", "Neutral"]
LIST_HIERARCHY = ["Squad", "Platoon", "Company", "Battalion"]
DICT_HIERARCHY_HP = {"Squad": 12, "Platoon": 40, "Company": 150, "Battalion": 600}
DICT_ZONE_COLORS = {"Red": "#FF0000", "Blue": "#0000FF", "Orange": "#FFA500", "Green": "#00FF00", "Cyan": "#00FFFF"}
DICT_PATH_COLORS = {"Red": "#FF0000", "Blue": "#0000FF", "Orange": "#FFA500", "Green": "#00FF00", "Cyan": "#00FFFF", "Brown": "#8B4513"}

# Stylesheets
STYLE_HEADER = f"color: {Theme.ACCENT_ALLY}; margin-bottom: 5px;"
STYLE_SCROLL = "QScrollArea { background: transparent; }"
STYLE_GRP_HEADER = f"color: {Theme.TEXT_DIM}; border-bottom: 1px solid {Theme.BORDER_STRONG}; padding-bottom: 4px; margin-top: 10px;"
STYLE_TIP = f"color: {Theme.TEXT_DIM}; font-style: italic;"
STYLE_DELETE_BTN = f"background-color: {Theme.ACCENT_ENEMY}; color: white; font-weight: bold; padding: 6px; border-radius: 4px;"
# -------------------------

class ObjectPropertiesWidget(QWidget):
    """
    Inspector Property Form: Displays properties for selected objects.
    """
    property_changed = pyqtSignal()
    
    def __init__(self, parent_window, state=None):
        super().__init__()
        self.parent_window = parent_window
        if state is None:
             raise ValueError("ObjectPropertiesWidget requires a 'state' object for initialization.")
        self.state = state
        self.current_hex = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignTop)
        
        self.props_label = QLabel(STR_TITLE_INSPECTOR)
        self.props_label.setFont(Theme.get_font(Theme.FONT_HEADER, 12, bold=True))
        self.props_label.setStyleSheet(STYLE_HEADER)
        layout.addWidget(self.props_label)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(STYLE_SCROLL)
        
        self.scroll_content = QWidget()
        self.form_layout = QVBoxLayout(self.scroll_content)
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.form_layout.setSpacing(15)
        self.form_layout.setAlignment(Qt.AlignTop)
        
        scroll.setWidget(self.scroll_content)
        layout.addWidget(scroll)

    def _add_group_header(self, title, accent=None):
        header = QLabel(title.upper())
        header.setFont(Theme.get_font(Theme.FONT_HEADER, 9, bold=True))
        header.setStyleSheet(STYLE_GRP_HEADER)
        self.form_layout.addWidget(header)

    def _add_property_card(self, widgets_list, title=None, accent=None):
        form_container = QWidget()
        form_layout = QFormLayout(form_container)
        form_layout.setContentsMargins(5, 5, 5, 5)
        form_layout.setSpacing(8)
        
        for label, widget in widgets_list:
            form_layout.addRow(label + ":", widget)
            
        self.form_layout.addWidget(form_container)

    def clear_content(self):
        self.props_label.setText(STR_TITLE_PROPERTIES)
        for i in reversed(range(self.form_layout.count())):
            item = self.form_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

    def show_default_mode_view(self, mode):
        self.clear_content()
        self.current_hex = None
        
        tip_label = QLabel()
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet(STYLE_TIP)
        
        if mode == "terrain":
            self.props_label.setText(STR_TITLE_WORLD_EDITOR)
            tip_label.setText(STR_TIP_TERRAIN)
        elif mode in ("area", "agents"):
            self.props_label.setText(STR_TITLE_SCENARIO_SETUP)
            tip_label.setText(STR_TIP_SCENARIO)
        else:
            self.props_label.setText(STR_TITLE_INSPECTOR)
            tip_label.setText(STR_TIP_DEFAULT)
            
        self.form_layout.addWidget(tip_label)

    def show_properties(self, kind, ident):
        self.clear_content()
        if not kind: return
            
        if kind == "map":
            coords_str = f"[{self.current_hex.q}, {self.current_hex.r}]" if self.current_hex else "-"
            self.props_label.setText(STR_TITLE_HEX_FMT.format(coords=coords_str))
            
            if self.current_hex:
                t_data = self.state.map.get_terrain(self.current_hex)
                self._add_group_header(STR_GRP_TERRAIN)
                
                type_combo = QComboBox()
                type_combo.addItems(LIST_TERRAIN_TYPES)
                type_combo.setCurrentText(t_data.get("type", "plains"))
                type_combo.currentTextChanged.connect(lambda t: self.update_terrain(self.current_hex, {"type": t}))
                
                elev_spin = QSpinBox()
                elev_spin.setRange(0, 5)
                elev_spin.setValue(t_data.get("elevation", 0))
                elev_spin.valueChanged.connect(lambda v: self.update_terrain(self.current_hex, {"elevation": v}))
                
                self._add_property_card([
                    (STR_LBL_TYPE, type_combo),
                    (STR_LBL_ELEVATION, elev_spin)
                ])
            
            self._add_group_header(STR_GRP_DIMENSIONS)
            w_spin = QSpinBox()
            w_spin.setRange(10, 500)
            w_spin.setValue(self.state.map.width)
            w_spin.valueChanged.connect(lambda v: setattr(self.state.map, 'width', v) or self.parent_window.hex_widget.update())
            
            h_spin = QSpinBox()
            h_spin.setRange(10, 500)
            h_spin.setValue(self.state.map.height)
            h_spin.valueChanged.connect(lambda v: setattr(self.state.map, 'height', v) or self.parent_window.hex_widget.update())
            
            self._add_property_card([
                (STR_LBL_WIDTH, w_spin),
                (STR_LBL_HEIGHT, h_spin)
            ])
            
        elif kind == "entity":
            ent = self.state.entity_manager.get_entity(ident)
            if not ent: return
            self.props_label.setText(ent.name)
            
            self._add_group_header(STR_GRP_IDENTITY)
            name_edit = QLineEdit(ent.name)
            name_edit.textChanged.connect(lambda t: self.update_entity(ent, t))
            
            type_combo = QComboBox()
            side_str = ent.get_attribute("side", "Attacker")
            if hasattr(self.state, 'data_controller') and self.state.data_controller:
                catalog = self.state.data_controller.agent_types.get(side_str, {})
                if catalog: type_combo.addItems(sorted(list(catalog.keys())))
            type_combo.setCurrentText(ent.get_attribute("type", ""))
            type_combo.currentTextChanged.connect(lambda t: ent.set_attribute("type", t))
            
            self._add_property_card([
                (STR_LBL_NAME, name_edit),
                (STR_LBL_AGENT_TYPE, type_combo)
            ])
            
            self._add_group_header(STR_GRP_COMMAND)
            side_combo = QComboBox()
            side_combo.addItems(LIST_SIDES)
            side_combo.setCurrentText(side_str)
            side_combo.currentTextChanged.connect(lambda t: ent.set_attribute("side", t) or self.parent_window.hex_widget.update())
            
            hier_combo = QComboBox()
            hier_combo.addItems(LIST_HIERARCHY)
            hier_combo.setCurrentText(ent.get_attribute("hierarchy", "Squad"))
            
            self._add_property_card([
                (STR_LBL_AFFILIATION, side_combo),
                (STR_LBL_HIERARCHY, hier_combo)
            ])
            
            self._add_group_header(STR_GRP_VITALS)
            hp_spin = QSpinBox()
            hp_spin.setRange(0, 1000)
            hp_spin.setValue(int(ent.get_attribute("personnel", 100)))
            hp_spin.valueChanged.connect(lambda v: ent.set_attribute("personnel", v))
            
            self._add_property_card([(STR_LBL_PERSONNEL, hp_spin)])

            def set_derived_health(hier_text):
                ent.set_attribute("hierarchy", hier_text)
                new_hp = DICT_HIERARCHY_HP.get(hier_text, 100)
                hp_spin.setValue(new_hp)
                ent.set_attribute("personnel", new_hp)

            hier_combo.currentTextChanged.connect(set_derived_health)
            self._add_delete_button(lambda: self._trigger_delete("entity", ident))

        elif kind == "zone":
            zdata = self.state.map.get_zones().get(ident)
            if not zdata: return
            self.props_label.setText(zdata.get("name"))
            
            self._add_group_header(STR_GRP_CONFIG)
            name_edit = QLineEdit(zdata.get("name", ""))
            name_edit.textChanged.connect(lambda t: self.update_zone(ident, {"name": t}))
            
            color_combo = QComboBox()
            for cname, ccode in DICT_ZONE_COLORS.items(): color_combo.addItem(cname, ccode)
            idx = color_combo.findData(zdata.get("color"))
            if idx >= 0: color_combo.setCurrentIndex(idx)
            color_combo.currentIndexChanged.connect(lambda i: self.update_zone(ident, {"color": color_combo.currentData()}))
            
            self._add_property_card([
                (STR_LBL_ZONE_NAME, name_edit),
                (STR_LBL_AURA_COLOR, color_combo)
            ])
            self._add_delete_button(lambda: self._trigger_delete("zone", ident))
            
        elif kind == "path":
            pdata = self.state.map.get_paths().get(ident)
            if not pdata: return
            self.props_label.setText(pdata.get('name', 'Path'))
            
            self._add_group_header(STR_GRP_CONFIG)
            name_edit = QLineEdit(pdata.get("name", ""))
            name_edit.textChanged.connect(lambda t: self.update_path(ident, {"name": t}))
            
            color_combo = QComboBox()
            for cname, ccode in DICT_PATH_COLORS.items(): color_combo.addItem(cname, ccode)
            idx = color_combo.findData(pdata.get("color"))
            if idx >= 0: color_combo.setCurrentIndex(idx)
            color_combo.currentIndexChanged.connect(lambda i: self.update_path(ident, {"color": color_combo.currentData()}))
            
            self._add_property_card([
                (STR_LBL_PATH_NAME, name_edit),
                (STR_LBL_VECTOR_COLOR, color_combo)
            ])

    def _add_delete_button(self, callback):
        del_btn = QPushButton(STR_BTN_DELETE)
        del_btn.setStyleSheet(STYLE_DELETE_BTN)
        del_btn.clicked.connect(callback)
        self.form_layout.addWidget(del_btn)

    def _trigger_delete(self, kind, ident):
        if kind == "entity":
            if hasattr(self.state, 'undo_stack'):
                from engine.core.undo_system import DeleteEntityCommand
                cmd = DeleteEntityCommand(self.state.map, self.state.entity_manager, ident)
                self.state.undo_stack.push(cmd)
            self.state.map.remove_entity(ident)
            self.state.entity_manager.unregister_entity(ident)
            mw = self.parent_window
            if hasattr(mw.hex_widget, 'active_tool') and mw.hex_widget.active_tool == mw.hex_widget.tools.get("cursor"):
                mw.hex_widget.active_tool.selected_entity_id = None
                mw.hex_widget.clear_selection()
            mw.hex_widget.update()
            if hasattr(mw, 'layer_manager'): mw.layer_manager.refresh_tree()
            self.show_default_mode_view(getattr(self.state, "app_mode", "terrain"))
            
        elif kind == "zone":
            zones = self.state.map.get_zones()
            if ident in zones:
                zdata = zones[ident]
                if hasattr(self.state, 'undo_stack'):
                    from engine.core.undo_system import RemoveZoneCommand
                    import copy
                    cmd = RemoveZoneCommand(self.state.map, ident, copy.deepcopy(zdata))
                    self.state.undo_stack.push(cmd)
                del zones[ident]
                mw = self.parent_window
                if hasattr(mw.hex_widget, 'active_tool') and mw.hex_widget.active_tool == mw.hex_widget.tools.get("cursor"):
                    mw.hex_widget.active_tool.selected_zone_id = None
                    mw.hex_widget.active_tool.invalidate_zone_index()
                    mw.hex_widget.clear_selection()
                mw.hex_widget.update()
                if hasattr(mw, 'layer_manager'): mw.layer_manager.refresh_tree()
                self.show_default_mode_view(getattr(self.state, "app_mode", "terrain"))

    def update_entity(self, ent, name):
        ent.name = name
        self.property_changed.emit()

    def update_path(self, pid, data):
        scen = self.state.map.active_scenario
        if pid in scen._paths: scen._paths[pid].update(data)
        self.property_changed.emit()
        self.parent_window.hex_widget.update()

    def update_zone(self, zid, data):
        self.state.map.update_zone(zid, data)
        self.property_changed.emit()
        self.parent_window.hex_widget.update()        

    def update_terrain(self, hex_obj, data):
        old_data = self.state.map.get_terrain(hex_obj)
        new_data = old_data.copy()
        new_data.update(data)
        if hasattr(self.state, "undo_stack"):
            from engine.core.undo_system import SetTerrainCommand
            cmd = SetTerrainCommand(self.state.map, hex_obj, new_data, old_data)
            self.state.undo_stack.push(cmd)
        self.state.map.set_terrain(hex_obj, new_data)
        self.parent_window.hex_widget.update()
