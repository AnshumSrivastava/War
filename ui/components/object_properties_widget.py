"""
FILE: ui/components/object_properties_widget.py
ROLE: The "Inspector" (Properties & Hierarchy).

DESCRIPTION:
This file creates the "Layers" panel you see on the left or right side of the screen.
It works like Photoshop or GIMP:
1. Scene Hierarchy: Shows a list (Tree) of everything on the map (Zones, Units, Borders).
2. Property Editor: When you click an item in the list, its 'Properties' 
   (like Name, Color, HP, or Elevation) appear in a form for you to edit.
3. Visibility Toggles: Has buttons to show/hide certain map features.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout, QLineEdit, QSpinBox, QComboBox, QSlider, QFrame, QProgressBar, QToolButton, QSizePolicy, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from engine.state.global_state import GlobalState
from ui.styles.theme import Theme

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
        """Standard property form layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignTop)
        
        # Header
        self.props_label = QLabel("OBJECT INSPECTOR")
        self.props_label.setFont(Theme.get_font(Theme.FONT_HEADER, 12, bold=True))
        self.props_label.setStyleSheet(f"color: {Theme.ACCENT_ALLY}; margin-bottom: 5px;")
        layout.addWidget(self.props_label)
        
        # Scroll Area for properties
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        
        self.scroll_content = QWidget()
        self.form_layout = QVBoxLayout(self.scroll_content)
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.form_layout.setSpacing(15)
        self.form_layout.setAlignment(Qt.AlignTop)
        
        scroll.setWidget(self.scroll_content)
        layout.addWidget(scroll)

    def _add_group_header(self, title, accent=None):
        """Simple bold header."""
        header = QLabel(title.upper())
        header.setFont(Theme.get_font(Theme.FONT_HEADER, 9, bold=True))
        header.setStyleSheet(f"color: {Theme.TEXT_DIM}; border-bottom: 1px solid {Theme.BORDER_STRONG}; padding-bottom: 4px; margin-top: 10px;")
        self.form_layout.addWidget(header)

    def _add_property_card(self, widgets_list, title=None, accent=None):
        """Groups property rows into a simple form block."""
        form_container = QWidget()
        form_layout = QFormLayout(form_container)
        form_layout.setContentsMargins(5, 5, 5, 5)
        form_layout.setSpacing(8)
        
        for label, widget in widgets_list:
            form_layout.addRow(label + ":", widget)
            
        self.form_layout.addWidget(form_container)

    def clear_content(self):
        """Clears all widgets from the form layout."""
        self.props_label.setText("PROPERTIES")
        for i in reversed(range(self.form_layout.count())):
            item = self.form_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

    def show_default_mode_view(self, mode):
        """Contextual tips for the current mode."""
        self.clear_content()
        self.current_hex = None
        
        tip_label = QLabel()
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-style: italic;")
        
        if mode == "terrain":
            self.props_label.setText("WORLD EDITOR")
            tip_label.setText("Select a hex to modify its terrain properties. Use the left toolbar for painting tools.")
        elif mode == "scenario":
            self.props_label.setText("SCENARIO SETUP")
            tip_label.setText("Deploy agents and define strategic zones. Change side filtering via the top tabs.")
        else:
            self.props_label.setText("INSPECTOR")
            tip_label.setText("Select an object to view and edit its properties.")
            
        self.form_layout.addWidget(tip_label)

    def show_properties(self, kind, ident):
        # Clear Layout
        self.clear_content()
        
        if not kind:
            return
            
        if kind == "map":
            coords_str = f"[{self.current_hex.q}, {self.current_hex.r}]" if self.current_hex else "-"
            self.props_label.setText(f"HEX {coords_str}")
            
            if self.current_hex:
                t_data = self.state.map.get_terrain(self.current_hex)
                self._add_group_header("Terrain Data")
                
                type_combo = QComboBox()
                types = ["plains", "forest", "water", "mountain", "urban"]
                type_combo.addItems(types)
                type_combo.setCurrentText(t_data.get("type", "plains"))
                type_combo.currentTextChanged.connect(lambda t: self.update_terrain(self.current_hex, {"type": t}))
                
                elev_spin = QSpinBox()
                elev_spin.setRange(0, 5)
                elev_spin.setValue(t_data.get("elevation", 0))
                elev_spin.valueChanged.connect(lambda v: self.update_terrain(self.current_hex, {"elevation": v}))
                
                self._add_property_card([
                    ("Type", type_combo),
                    ("Elevation", elev_spin)
                ])
            
            # Global Dimensions
            self._add_group_header("Map Dimensions")
            w_spin = QSpinBox()
            w_spin.setRange(10, 500)
            w_spin.setValue(self.state.map.width)
            w_spin.valueChanged.connect(lambda v: setattr(self.state.map, 'width', v) or self.parent_window.hex_widget.update())
            
            h_spin = QSpinBox()
            h_spin.setRange(10, 500)
            h_spin.setValue(self.state.map.height)
            h_spin.valueChanged.connect(lambda v: setattr(self.state.map, 'height', v) or self.parent_window.hex_widget.update())
            
            self._add_property_card([
                ("Width", w_spin),
                ("Height", h_spin)
            ])
            
        elif kind == "entity":
            ent = self.state.entity_manager.get_entity(ident)
            if not ent: return
            self.props_label.setText(ent.name)
            
            self._add_group_header("Identity")
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
                ("Name", name_edit),
                ("Agent Type", type_combo)
            ])
            
            self._add_group_header("Command")
            side_combo = QComboBox()
            side_combo.addItems(["Attacker", "Defender", "Neutral"])
            side_combo.setCurrentText(side_str)
            side_combo.currentTextChanged.connect(lambda t: ent.set_attribute("side", t) or self.parent_window.hex_widget.update())
            
            hier_combo = QComboBox()
            hier_combo.addItems(["Squad", "Platoon", "Company", "Battalion"])
            hier_combo.setCurrentText(ent.get_attribute("hierarchy", "Squad"))
            
            self._add_property_card([
                ("Affiliation", side_combo),
                ("Hierarchy", hier_combo)
            ])
            
            self._add_group_header("Vitals")
            hp_spin = QSpinBox()
            hp_spin.setRange(0, 1000)
            hp_spin.setValue(int(ent.get_attribute("personnel", 100)))
            hp_spin.valueChanged.connect(lambda v: ent.set_attribute("personnel", v))
            
            self._add_property_card([("Personnel", hp_spin)])

            def set_derived_health(hier_text):
                ent.set_attribute("hierarchy", hier_text)
                health_map = {"Squad": 12, "Platoon": 40, "Company": 150, "Battalion": 600}
                new_hp = health_map.get(hier_text, 100)
                hp_spin.setValue(new_hp)
                ent.set_attribute("personnel", new_hp)

            hier_combo.currentTextChanged.connect(set_derived_health)

        elif kind == "zone":
            zdata = self.state.map.get_zones().get(ident)
            if not zdata: return
            self.props_label.setText(zdata.get("name"))
            
            self._add_group_header("Configuration")
            name_edit = QLineEdit(zdata.get("name", ""))
            name_edit.textChanged.connect(lambda t: self.update_zone(ident, {"name": t}))
            
            color_combo = QComboBox()
            colors = {"Red": "#FF0000", "Blue": "#0000FF", "Orange": "#FFA500", "Green": "#00FF00", "Cyan": "#00FFFF"}
            for cname in colors: color_combo.addItem(cname, colors[cname])
            idx = color_combo.findData(zdata.get("color"))
            if idx >= 0: color_combo.setCurrentIndex(idx)
            color_combo.currentIndexChanged.connect(lambda i: self.update_zone(ident, {"color": color_combo.currentData()}))
            
            self._add_property_card([
                ("Zone Name", name_edit),
                ("Aura Color", color_combo)
            ])
            
        elif kind == "path":
            pdata = self.state.map.get_paths().get(ident)
            if not pdata: return
            self.props_label.setText(pdata.get('name', 'Path'))
            
            self._add_group_header("Configuration")
            name_edit = QLineEdit(pdata.get("name", ""))
            name_edit.textChanged.connect(lambda t: self.update_path(ident, {"name": t}))
            
            color_combo = QComboBox()
            colors = {"Red": "#FF0000", "Blue": "#0000FF", "Orange": "#FFA500", "Green": "#00FF00", "Cyan": "#00FFFF", "Brown": "#8B4513"}
            for cname in colors: color_combo.addItem(cname, colors[cname])
            idx = color_combo.findData(pdata.get("color"))
            if idx >= 0: color_combo.setCurrentIndex(idx)
            color_combo.currentIndexChanged.connect(lambda i: self.update_path(ident, {"color": color_combo.currentData()}))
            
            self._add_property_card([
                ("Path Name", name_edit),
                ("Vector Color", color_combo)
            ])


    def update_entity(self, ent, name):
        ent.name = name
        self.property_changed.emit()

    def update_path(self, pid, data):
        scen = self.state.map.active_scenario
        if pid in scen._paths:
            scen._paths[pid].update(data)
        self.property_changed.emit()
        self.parent_window.hex_widget.update()

    def update_zone(self, zid, data):
        self.state.map.update_zone(zid, data)
        self.property_changed.emit()
        self.parent_window.hex_widget.update()        

    def update_terrain(self, hex_obj, data):
        """Update terrain properties with Undo support."""
        old_data = self.state.map.get_terrain(hex_obj)
        
        # Merge changes
        new_data = old_data.copy()
        new_data.update(data)
        
        # Undo Command
        if hasattr(self.state, "undo_stack"):
            from engine.core.undo_system import SetTerrainCommand
            cmd = SetTerrainCommand(self.state.map, hex_obj, new_data, old_data)
            self.state.undo_stack.push(cmd)
            
        self.state.map.set_terrain(hex_obj, new_data)
        self.parent_window.hex_widget.update()

