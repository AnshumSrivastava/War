"""
FILE: engine/ai/encoder.py
ROLE: The "Translator" (State Representation).

DESCRIPTION:
This module handles state encoding for Reinforcement Learning.
It includes a TileCoder for scaling state spaces using multiple 
overlapping tilings and hashing.
"""
import numpy as np

class TileCoder:
    """
    Implements Tile Coding (a form of coarse coding) to discretize 
    continuous or large discrete spaces using multiple overlapping grids.
    """
    def __init__(self, num_tilings, bins_per_dim, x_range, y_range, offset_type="random"):
        self.num_tilings = num_tilings
        self.bins_per_dim = bins_per_dim
        self.x_range = x_range
        self.y_range = y_range
        
        self.tile_width = (x_range[1] - x_range[0]) / bins_per_dim
        self.tile_height = (y_range[1] - y_range[0]) / bins_per_dim
        
        # Offsets for each tiling
        if offset_type == "random":
            self.offsets = np.random.uniform(0, 1, (num_tilings, 2))
        else:
            # Uniformly distributed offsets
            shift = 1.0 / num_tilings
            self.offsets = np.array([[i * shift, i * shift] for i in range(num_tilings)])

    def get_tiles(self, x, y):
        """Returns the active tile indices for a given coordinate."""
        tiles = []
        for i in range(self.num_tilings):
            off_x, off_y = self.offsets[i]
            
            # Rescale to grid units
            tx = (x - self.x_range[0]) / self.tile_width + off_x
            ty = (y - self.y_range[0]) / self.tile_height + off_y
            
            # Integer indices
            idx_x = int(np.floor(tx))
            idx_y = int(np.floor(ty))
            
            # Combine into a unique ID (hash-like)
            # We use a large prime multiplier to avoid collisions
            tile_id = (i, idx_x, idx_y)
            tiles.append(hash(tile_id))
            
        return tiles

class StateActionEncoder:
    """
    The "Master Translator". 
    Converts map state and entity attributes into features for RL.
    """
    CASUALTY_STATES = 4
    REWARD_STATES = 3
    
    def __init__(self, rows=20, cols=20, use_tile_coding=True):
        self.rows = rows
        self.cols = cols
        self.grid_size = rows * cols
        self.use_tile_coding = use_tile_coding
        
        if use_tile_coding:
            # 8 tilings of 10x10 over the map area
            self.tile_coder = TileCoder(
                num_tilings=8,
                bins_per_dim=10, 
                x_range=(0, cols), 
                y_range=(0, rows),
                offset_type="uniform"
            )
            # We use hashing to map to a fixed state size (e.g., 2^12 = 4096)
            self.state_size = 4096 
        else:
            self.state_size = self.grid_size * self.CASUALTY_STATES * self.REWARD_STATES
    
    @classmethod
    def from_map(cls, game_map):
        return cls(rows=game_map.height, cols=game_map.width)
    
    def encode_casualty(self, current_health, max_health):
        if max_health <= 0: return 3
        ratio = current_health / max_health
        if ratio > 0.75: return 0 
        if ratio > 0.50: return 1
        if ratio > 0.25: return 2
        return 3
    
    def encode_reward(self, cumulative_reward):
        if cumulative_reward < -10: return 0
        if cumulative_reward > 10: return 2
        return 1
    
    def get_features(self, entity, game_map, cumulative_reward=0, data_controller=None):
        """
        Returns a list of active feature indices (Tile Coding + Attributes).
        """
        from engine.core.hex_math import HexMath
        hex_pos = game_map.get_entity_position(entity.id)
        if hex_pos is None: return []
        
        col, row = HexMath.cube_to_offset(hex_pos)
        
        # 1. Spatial Features (Tile Coding)
        active_tiles = self.tile_coder.get_tiles(col, row)
        
        # 2. Attribute Features
        if data_controller:
            config = data_controller.resolve_unit_config(entity)
            max_h = config.get("personnel", config.get("max_health", 100))
        else:
            max_h = 100
        current_h = int(entity.get_attribute("personnel", entity.get_attribute("health", max_h)))
        cas_state = self.encode_casualty(current_h, max_h)
        rew_state = self.encode_reward(cumulative_reward)
        
        # Combine tiles with attributes into a final feature list
        # We hash the (Tile_ID, Casualty, Reward) to stay within the hash space
        features = []
        for tile_hash in active_tiles:
            # Shift features by attributes to create unique context-aware tiles
            feature_idx = (tile_hash ^ hash((cas_state, rew_state))) % self.state_size
            features.append(abs(feature_idx))
            
        return features

    def get_combined_state(self, entity, game_map, cumulative_reward=0, data_controller=None):
        """Legacy support for single-index Q-tables."""
        features = self.get_features(entity, game_map, cumulative_reward, data_controller)
        return features[0] if features else 0

    def decode_state(self, state_idx):
        """Decoding is limited with hashing/tile coding."""
        return {"id": state_idx, "info": "Tile Coded State"}