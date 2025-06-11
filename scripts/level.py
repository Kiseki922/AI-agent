import pygame
from pytmx.util_pygame import load_pygame

class TMXMapLoader:
    def __init__(self, game):
        self.game = game
        self.sprite_group = game.sprite_group
        self.collision_sprites = game.collision_sprites
        
    def load_map(self, map_path):
        """
        Load a TMX map file and create all necessary tiles and collision objects
        
        Args:
            map_path (str): Path to the TMX map file
        """
        # Load the TMX data
        tmx_data = load_pygame(map_path)
        
        # Process tile layers
        self.tile_layers(tmx_data)
        
        # Process object groups
        self.object(tmx_data)
        
        return tmx_data
        # 在level.py中，确保在object方法中处理对象组
    def object(self, tmx_data):
        """Process all object groups in the TMX map"""
        for obj_group in tmx_data.objectgroups:
            print(f"Processing object group: {obj_group.name}")  # 打印对象组名称以调试
            
            for obj in obj_group:
                if obj.image:
                    pos = obj.x, obj.y
                    print(f"  - Object at {pos}")  # 打印对象位置以调试
                    
                    # 处理每个对象组类型
                    if obj_group.name == "bed":
                        self.tile(pos, obj.image, [self.sprite_group])
                    elif obj_group.name == "toilet":
                        self.tile(pos, obj.image, [self.sprite_group])
                    elif obj_group.name == "ref":
                        self.tile(pos, obj.image, [self.sprite_group])
                    elif obj_group.name == "chair_in_fornt_of_desk":
                        self.tile(pos, obj.image, [self.sprite_group])
                    elif obj_group.name == "sofa in fornt of TV":
                        self.tile(pos, obj.image, [self.sprite_group])
                    elif obj_group.name == "bookshelf":
                        self.tile(pos, obj.image, [self.sprite_group])
                    elif obj_group.name == "window":
                        self.tile(pos, obj.image, [self.sprite_group])
                    else:
                        self.tile(pos, obj.image, [self.sprite_group]) 
    
    def tile_layers(self, tmx_data):
        """Process all tile layers in the TMX map"""
        for layer in tmx_data.visible_layers:
            if hasattr(layer, 'data'):  # This checks if it's a tile layer
                print(f"Processing tile group: {layer.name}")
                for x, y, surf in layer.tiles():
                    pos = (x * 32, y * 32)
                    # Handle each tile group type separately
                    if layer.name == "wall":
                        self.tile(pos, surf, [self.sprite_group, self.collision_sprites])
                    elif layer.name == "floor":# Process "floor" tiles
                        self.tile(pos, surf, [self.sprite_group])  # Only add to sprite group
                    else:
                        self.tile(pos, surf, [self.sprite_group])
    
    def tile(self, pos, surf, groups):
        """Create a tile sprite at the given position with the given surface"""
        from scripts.tilemaps import Tile  # Import here to avoid circular imports
        return Tile(pos=pos, surf=surf, groups=groups)

#備註
#要手動設定固定位置讓NPC站立