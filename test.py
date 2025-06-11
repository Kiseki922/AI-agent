import os
import xml.etree.ElementTree as ET

class Game:
    def __init__(self):
        map_path = 'art/image/tiles/tiles/tmx/testmap.tmx'

        if not os.path.exists(map_path):
            print(f"地图文件未找到: {map_path}")
            return

        print("地图加载成功！")
        print("图层结构：")
        self.parse_tmx(map_path)

    def parse_tmx(self, map_path):
        """解析 TMX 文件，正确获取图层层级"""
        tree = ET.parse(map_path)  # 解析 XML
        root = tree.getroot()

        # 从 <map> 标签开始递归
        self.print_layers(root, indent=0)

    def print_layers(self, parent, indent):
        """递归打印层级结构，包括 group, objectgroup 和 layer"""
        for element in parent:
            if element.tag == "layer":
                print("  " * indent + f"- Layer: {element.get('name')}")
            elif element.tag == "group":
                print("  " * indent + f"- Group: {element.get('name')}")
                self.print_layers(element, indent + 1)  # 递归处理嵌套的 group 或 layer
            elif element.tag == "objectgroup":
                print("  " * indent + f"- Object Group: {element.get('name')}")
                for obj in element:
                    if obj.tag == "object":
                        print("  " * (indent + 1) + f"- Object ID: {obj.get('id')}, GID: {obj.get('gid')}, X: {obj.get('x')}, Y: {obj.get('y')}, Width: {obj.get('width')}, Height: {obj.get('height')}")

Game()

