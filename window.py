import sys
import pygame
from scripts.player import PhysicalEntity
from scripts.utils import load_image, load_images
from pytmx.util_pygame import load_pygame
from scripts.tilemaps import Tile
from scripts.level import TMXMapLoader
from scripts.Agents.npc import NPCController


class game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption("專題") #window title  

        self.screen = pygame.display.set_mode((800, 600))
        
        self.clock = pygame.time.Clock() #clock control variable to control the frame rate
        
        self.movements = [False,False,False,False]
        
        self.sprite_group = pygame.sprite.Group()    #group to store the sprites
        
        self.collision_sprites = pygame.sprite.Group()  # Group for collision tiles
        #assets
        self.assets = {
            'npc' : load_image('entities/npc.png'),
            'player': load_image('entities/player.png')
        } #load the image
        
        self.player = PhysicalEntity(self, 'player', (50,50), (8,15))
        
        self.npc_controller = None  # 将在加载地图后初始化
        #pytmx test
        #get layers
        # print(tmx_data.layers)
        # for layer in tmx_data.layers: #get visable layers
        #     print(layer)
        # print(tmx_data.layernames) #get all layer names
        # print(tmx_data.get_layer_by_name('floor')) #get layer by name
        
        # for obj in tmx_data.objectgroups: #get object layers
        #     print(obj)
        # #get tiled
        # layers = tmx_data.get_layer_by_name('floor')
        # for x,y,surf in layers.tiles(): #get all the imformation of the tile
        #     print(x*32) #size of the tileset to get acually position
        #     print(y*32)
        #     print(surf)        
        
        # object_layer = tmx_data.get_layer_by_name('objects') #get the object layer
        # print(object_layer)
        
        # 在加载完地图后初始化NPC控制器和NPC
        self.map_loader = TMXMapLoader(self)
        self.tmx_data = self.map_loader.load_map('art/image/tiles/tiles/tmx/testmap.tmx')

        # 初始化NPC控制器
        self.npc_controller = NPCController(self)
        # 创建一个NPC
        self.npc = self.npc_controller.create_npc("npc1", "npc", (50, 50))

        # 添加一个变量来存储用户输入的命令
        self.command_input = ""
        self.command_active = False
        
        '''
            self.img_pos[1] += self.movements[1]*3 - self.movements[0]*3 #move foward or backward
            self.img_pos[0] += self.movements[3]*3 - self.movements[2]*3 #move left or right
            self.screen.blit(self.img, self.img_pos)
            '''
            
        '''
            img_r = pygame.Rect(self.img_pos[0], self.img_pos[1],self.img.get_width(),self.img.get_height()) 
            
            
            #collision test: draw the rectangle
            
            if img_r.colliderect(self.collisions_area):
                pygame.draw.rect(self.screen, (255,0,0), self.collisions_area)
            else:
                pygame.draw.rect(self.screen, (0,255,0), self.collisions_area)
        '''
            
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()  # exit the program

                # 处理命令输入模式的开关
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:  # Enter键
                        if self.command_active:  # 如果命令模式是活跃的
                            self.process_command(self.command_input)
                            self.command_input = ""
                            self.command_active = False
                        else:
                            self.command_active = True
                    
                    elif event.key == pygame.K_ESCAPE:  # ESC键退出命令模式
                        self.command_input = ""
                        self.command_active = False
                    
                    elif self.command_active:  # 如果命令模式是活跃的，收集输入
                        if event.key == pygame.K_BACKSPACE:
                            self.command_input = self.command_input[:-1]
                        else:
                            self.command_input += event.unicode
                    
                    # 常规移动控制，仅在非命令模式下
                    elif not self.command_active:
                        if event.key == pygame.K_w:
                            self.movements[0] = True
                        elif event.key == pygame.K_s:
                            self.movements[1] = True
                        elif event.key == pygame.K_a:
                            self.movements[2] = True
                        elif event.key == pygame.K_d:
                            self.movements[3] = True

                elif event.type == pygame.KEYUP and not self.command_active:
                    if event.key == pygame.K_w:
                        self.movements[0] = False
                    elif event.key == pygame.K_s:
                        self.movements[1] = False
                    elif event.key == pygame.K_a:
                        self.movements[2] = False
                    elif event.key == pygame.K_d:
                        self.movements[3] = False

            self.screen.fill((50, 50, 50))  # background color and clear the screen
            
            # 更新NPC
            if self.npc_controller:
                self.npc_controller.update_all()
            
            # Update the player movement
            self.player.update((self.movements[1] * 3 - self.movements[0] * 3,
                                self.movements[3] * 3 - self.movements[2] * 3))

            
            # Drawing the tilemap
            self.sprite_group.draw(self.screen)  # Draw all tiles and objects
            self.player.render(self.screen)  # Draw the player

            # 如果命令模式是活跃的，显示命令输入框
            if self.command_active:
                # 创建一个命令输入框
                font = pygame.font.SysFont(None, 24)
                command_surface = font.render(f"> {self.command_input}", True, (255, 255, 255))
                self.screen.blit(command_surface, (10, 10))

            # Update the screen by drawing the 'display' surface onto the screen
            pygame.display.update()  # Update the screen
            self.clock.tick(60)  # 60 frames

    def process_command(self, command):
        """处理用户输入的命令"""
        print(f"处理命令: {command}")  # 添加调试输出
        
        if not command:
            return
        
        # 分割命令字符串
        parts = command.strip().split()
        
        # 命令需要至少有一个参数
        if len(parts) < 1:
            print("无效命令")
            return
        
        # 打印当前所有可用的对象组
        print("可用对象组:")
        for group in self.tmx_data.objectgroups:
            print(f"  - {group.name}")
        
        # 处理 "goto" 命令
        if parts[0].lower() == "goto" and len(parts) >= 2:
            object_name = " ".join(parts[1:])  # 合并可能包含空格的对象名称
            print(f"尝试移动到对象: {object_name}")
            success = self.npc_controller.move_npc_to_object("npc1", object_name)
            if success:
                print("命令执行成功")
            else:
                print("命令执行失败")
        
        # 处理 "goto_tile" 命令
        elif parts[0].lower() == "goto_tile" and len(parts) >= 4:
            layer_name = parts[1]
            try:
                tile_x = int(parts[2])
                tile_y = int(parts[3])
                success = self.npc_controller.move_npc_to_tile("npc1", layer_name, tile_x, tile_y)
                if success:
                    print("命令执行成功")
                else:
                    print("命令执行失败")
            except ValueError:
                print("无效的坐标值")
        
        else:
            print(f"未知命令: {command}")

game().run()
