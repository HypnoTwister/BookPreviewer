import subprocess
import os
import shutil

Resource = 'resources/writingcounter.csv'

def build():
    try:
        # 运行 pyinstaller 命令
        result = subprocess.run(['pyinstaller', '--noconfirm', 'BookPreviewer.spec'], check=True)
        print("Build completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error: {e}")

if __name__ == "__main__":
    # print(__file__)
    dir = os.path.dirname(__file__)
    resource_file = f"{dir}/dist/BookPreviewer/_internal/{Resource}".replace('\\', '/')
    # print(resource_file)
    if os.path.exists(resource_file):
        print(f'File exists:{resource_file}')
        shutil.copy2(resource_file, f"{dir}/{Resource}")
    build()