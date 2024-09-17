import subprocess

def build():
    try:
        # 运行 pyinstaller 命令
        result = subprocess.run(['pyinstaller', '--noconfirm', 'BookPreviewer.spec'], check=True)
        print("Build completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error: {e}")

if __name__ == "__main__":
    build()