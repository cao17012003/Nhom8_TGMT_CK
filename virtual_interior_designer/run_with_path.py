def main():
    import sys
    import os
    
    # Thêm đường dẫn của thư mục cha vào sys.path
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(parent_dir)
    
    # Thêm đường dẫn đến lama-with-refiner
    lama_dir = os.path.join(parent_dir, 'lama-with-refiner')
    sys.path.append(lama_dir)
    
    # Tiếp tục với mã Django bình thường
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'virtual_interior_designer.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main() 