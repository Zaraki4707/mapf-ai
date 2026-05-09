import os
from typing import List, Dict

def list_predefined_maps() -> List[Dict[str, str]]:
    maps_info = []
    search_dirs = {
        'Common Maps': r'E:\Intro_to_ai_Project\maps',
        'Widjdane''s Maps': r'E:\Intro_to_ai_Project\widjdane_chouali'
    }
    for category, directory in search_dirs.items():
        if os.path.exists(directory):
            for file in os.listdir(directory):
                if file.endswith('.txt'):
                    maps_info.append({
                        'id': f'{category.lower().replace(" ", "_")}_{file}',
                        'name': file,
                        'category': category,
                        'path': os.path.join(directory, file)
                    })
    return maps_info

def parse_map_file(file_path: str):
    if not os.path.exists(file_path):
        return None
    obstacles = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.rstrip('\r\n') for line in f if line.strip()]
            height = len(lines)
            width = max(len(line) for line in lines) if height > 0 else 0
            for y, line in enumerate(lines):
                for x, char in enumerate(line):
                    if char == 'T':
                        obstacles.append([x, y])
        return {
            'grid_height': height,
            'grid_width': width,
            'obstacles': obstacles
        }
    except Exception as e:
        print(f'Error: {e}')
        return None
