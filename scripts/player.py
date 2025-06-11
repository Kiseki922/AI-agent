import pygame
import sys

class PhysicalEntity(pygame.sprite.Sprite):
    def __init__(self, game, e_type, pos, size):
        super().__init__()  # 初始化 Sprite
        self.game = game
        self.e_type = e_type
        self.size = size
        self.velocity = [0, 0]
        
        # 轉換為格子位置
        self.grid_pos = [pos[0] // size[0], pos[1] // size[1]]
        
        # 實際像素位置
        self.pos = [self.grid_pos[0] * size[0], self.grid_pos[1] * size[1]]
        
        # 設定圖像與矩形
        self.image = game.assets[e_type]  # 確保 assets 正確載入
        self.rect = self.image.get_rect(topleft=self.pos)
        self.hitbox = self.rect.copy().inflate((-16,-16)) #碰撞箱
        
        # 移動方向枚舉 - 只允許四個方向
        self.DIRECTION_UP = 0
        self.DIRECTION_DOWN = 1
        self.DIRECTION_LEFT = 2
        self.DIRECTION_RIGHT = 3
        
        # 當前移動方向
        self.current_direction = None
        
        # 移動冷卻時間 (避免移動過快)
        self.move_cooldown = 0
        self.move_cooldown_time = 10  # 移動間隔的幀數
    
    def update(self, movement=(0, 0)):
        # 減少移動冷卻計時器
        if self.move_cooldown > 0:
            self.move_cooldown -= 1
            return
            
        # window_test.py 中傳入的 movement 格式為 (垂直移動, 水平移動)
        # 垂直移動：負值是向上，正值是向下
        # 水平移動：負值是向左，正值是向右
        
        # 優先處理垂直方向移動
        if movement[0] < 0:  # 向上
            self.try_move(self.DIRECTION_UP)
        elif movement[0] > 0:  # 向下
            self.try_move(self.DIRECTION_DOWN)
        # 然後處理水平方向移動
        elif movement[1] < 0:  # 向左
            self.try_move(self.DIRECTION_LEFT)
        elif movement[1] > 0:  # 向右
            self.try_move(self.DIRECTION_RIGHT)
    
    def try_move(self, direction):
        # 設置移動冷卻
        self.move_cooldown = self.move_cooldown_time
        
        # 保存當前網格位置
        old_grid_pos = self.grid_pos.copy()
        
        # 根據方向計算新的網格位置
        if direction == self.DIRECTION_UP:
            new_grid_pos = [self.grid_pos[0], self.grid_pos[1] - 1]
        elif direction == self.DIRECTION_DOWN:
            new_grid_pos = [self.grid_pos[0], self.grid_pos[1] + 1]
        elif direction == self.DIRECTION_LEFT:
            new_grid_pos = [self.grid_pos[0] - 1, self.grid_pos[1]]
        elif direction == self.DIRECTION_RIGHT:
            new_grid_pos = [self.grid_pos[0] + 1, self.grid_pos[1]]
        else:
            return False
            
        # 更新方向
        self.current_direction = direction
        
        # 計算新的像素位置
        new_pos = [new_grid_pos[0] * self.size[0], new_grid_pos[1] * self.size[1]]
        
        # 暫時更新位置和碰撞盒
        self.grid_pos = new_grid_pos
        self.pos = new_pos
        self.hitbox.topleft = self.pos
        self.rect.topleft = self.pos
        
        # 檢查碰撞
        if self.check_collision():
            # 如果碰撞，恢復原位置
            self.grid_pos = old_grid_pos
            self.pos = [old_grid_pos[0] * self.size[0], old_grid_pos[1] * self.size[1]]
            self.hitbox.topleft = self.pos
            self.rect.topleft = self.pos
            return False
            
        return True
    
    def check_collision(self):
        """檢查碰撞並返回是否發生碰撞"""
        for sprite in self.game.collision_sprites:
            if self.hitbox.colliderect(sprite.rect):
                return True
        return False
    
    def render(self, surf):
        surf.blit(self.image, self.rect.topleft)