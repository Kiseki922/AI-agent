import pygame
import sys
import os

def test_emoji_support():
    """测试系统是否支持emoji显示"""
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Emoji Support Test")
    
    # 测试的emoji列表
    test_emojis = ["🛏️", "🧊", "🛋️", "📺", "💺", "🚶", "😴", "💬"]
    
    # 尝试不同的字体
    fonts_to_test = [
        # Windows
        ("Segoe UI Emoji", None),
        ("seguiemj.ttf", "C:/Windows/Fonts/seguiemj.ttf"),
        # macOS  
        ("Apple Color Emoji", "/System/Library/Fonts/Apple Color Emoji.ttc"),
        # Linux
        ("Noto Color Emoji", "/usr/share/fonts/truetype/noto-color-emoji/NotoColorEmoji.ttf"),
        # 系统默认
        ("System Default", None)
    ]
    
    print("=== Emoji Font Support Test ===")
    
    y_offset = 50
    working_fonts = []
    
    for font_name, font_path in fonts_to_test:
        print(f"\nTesting {font_name}...")
        
        # 尝试加载字体
        font = None
        try:
            if font_path and os.path.exists(font_path):
                font = pygame.font.Font(font_path, 32)
                print(f"  ✓ Font file found: {font_path}")
            elif font_name == "System Default":
                font = pygame.font.SysFont(['segoeuiemoji', 'applesymbols', 'symbola'], 32)
                print(f"  ✓ Using system font")
            else:
                font = pygame.font.SysFont([font_name.lower().replace(' ', '')], 32)
                print(f"  ✓ Using system font: {font_name}")
        except Exception as e:
            print(f"  ✗ Failed to load font: {e}")
            continue
        
        if font:
            # 测试emoji渲染
            emoji_works = 0
            for emoji in test_emojis:
                try:
                    surface = font.render(emoji, True, (255, 255, 255))
                    if surface.get_width() > 10:  # 如果宽度足够，说明渲染成功
                        emoji_works += 1
                except:
                    pass
            
            success_rate = emoji_works / len(test_emojis) * 100
            print(f"  Emoji success rate: {success_rate:.1f}% ({emoji_works}/{len(test_emojis)})")
            
            if success_rate > 50:
                working_fonts.append((font_name, font_path, font, success_rate))
            
            # 在屏幕上显示测试结果
            text_surface = pygame.font.SysFont(None, 24).render(
                f"{font_name}: {success_rate:.1f}%", True, (255, 255, 255)
            )
            screen.blit(text_surface, (10, y_offset))
            
            # 显示emoji测试
            x_offset = 300
            for emoji in test_emojis:
                try:
                    emoji_surface = font.render(emoji, True, (255, 255, 255))
                    screen.blit(emoji_surface, (x_offset, y_offset))
                    x_offset += 40
                except:
                    # 如果emoji失败，显示X
                    x_surface = pygame.font.SysFont(None, 24).render("X", True, (255, 0, 0))
                    screen.blit(x_surface, (x_offset, y_offset))
                    x_offset += 40
            
            y_offset += 40
    
    # 显示推荐设置
    if working_fonts:
        best_font = max(working_fonts, key=lambda x: x[3])
        print(f"\n=== RECOMMENDATION ===")
        print(f"Best font: {best_font[0]} (Success rate: {best_font[3]:.1f}%)")
        if best_font[1]:
            print(f"Font path: {best_font[1]}")
        print(f"Use display_mode = 'emoji' in your code")
    else:
        print(f"\n=== RECOMMENDATION ===")
        print(f"No working emoji fonts found.")
        print(f"Use display_mode = 'text' in your code")
    
    # 显示说明
    instruction_text = [
        "=== Instructions ===",
        "If you see emojis clearly, your system supports emoji fonts.",
        "If you see 'X' marks, those emojis failed to render.",
        "Press SPACE to toggle between emoji and text mode demo",
        "Press ESC to exit"
    ]
    
    for i, text in enumerate(instruction_text):
        text_surface = pygame.font.SysFont(None, 20).render(text, True, (200, 200, 200))
        screen.blit(text_surface, (10, 450 + i * 25))
    
    pygame.display.flip()
    
    # 等待用户输入
    clock = pygame.time.Clock()
    demo_mode = 'emoji'  # 'emoji' or 'text'
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return
                elif event.key == pygame.K_SPACE:
                    demo_mode = 'text' if demo_mode == 'emoji' else 'emoji'
                    print(f"Switched to {demo_mode} mode")
                    
                    # 清除屏幕并重新绘制
                    screen.fill((0, 0, 0))
                    
                    # 重新绘制字体测试结果
                    y_offset = 50
                    for font_name, font_path, font, success_rate in working_fonts:
                        text_surface = pygame.font.SysFont(None, 24).render(
                            f"{font_name}: {success_rate:.1f}%", True, (255, 255, 255)
                        )
                        screen.blit(text_surface, (10, y_offset))
                        
                        # 显示demo
                        x_offset = 300
                        for emoji in test_emojis:
                            if demo_mode == 'emoji':
                                try:
                                    emoji_surface = font.render(emoji, True, (255, 255, 255))
                                    screen.blit(emoji_surface, (x_offset, y_offset))
                                except:
                                    x_surface = pygame.font.SysFont(None, 24).render("X", True, (255, 0, 0))
                                    screen.blit(x_surface, (x_offset, y_offset))
                            else:
                                # 显示文字替代
                                text_alternatives = ["BED", "ICE", "SOFA", "TV", "DESK", "WALK", "SLEEP", "CHAT"]
                                idx = test_emojis.index(emoji)
                                if idx < len(text_alternatives):
                                    text_surface = pygame.font.SysFont(None, 16).render(
                                        text_alternatives[idx], True, (255, 255, 100)
                                    )
                                    screen.blit(text_surface, (x_offset, y_offset))
                            x_offset += 40
                        
                        y_offset += 40
                    
                    # 重新显示说明
                    for i, text in enumerate(instruction_text):
                        text_surface = pygame.font.SysFont(None, 20).render(text, True, (200, 200, 200))
                        screen.blit(text_surface, (10, 450 + i * 25))
                    
                    # 显示当前模式
                    mode_text = f"Current mode: {demo_mode.upper()}"
                    mode_surface = pygame.font.SysFont(None, 24).render(mode_text, True, (255, 255, 0))
                    screen.blit(mode_surface, (10, 400))
                    
                    pygame.display.flip()
        
        clock.tick(60)

if __name__ == "__main__":
    test_emoji_support()