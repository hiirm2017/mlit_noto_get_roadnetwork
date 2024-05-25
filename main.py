import requests
import os
import zipfile
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.animation import FuncAnimation
import imageio
import numpy as np
from datetime import datetime, timedelta

# 共通のベースフォルダ．データ期間の設定
base_folder = "/Users/makoto/Downloads"
start_date = "20240112"
end_date = "20240520"

def download_zip_files(start_date, end_date, url_pattern, destination_folder):
    date_format = "%Y%m%d"
    start = datetime.strptime(start_date, date_format)
    end = datetime.strptime(end_date, date_format)
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    
    current_date = start
    while current_date <= end:
        date_str = current_date.strftime("%y%m%d")
        file_url = url_pattern.format(date_str)
        response = requests.get(file_url)
        if response.status_code == 200:
            file_name = f"data_{date_str}.zip"
            full_path = os.path.join(destination_folder, file_name)
            with open(full_path, 'wb') as file:
                file.write(response.content)
            print(f"Downloaded {file_name} to {full_path}")
        else:
            print(f"The file does not exist {file_url}")
        current_date += timedelta(days=1)

def extract_and_plot_geojson(start_date, end_date, zip_path_pattern, output_folder_geojson, output_folder_images):
    current_date = datetime.strptime(start_date, "%Y%m%d")
    end_date = datetime.strptime(end_date, "%Y%m%d")
    if not os.path.exists(output_folder_geojson):
        os.makedirs(output_folder_geojson)
    if not os.path.exists(output_folder_images):
        os.makedirs(output_folder_images)

    while current_date <= end_date:
        zip_filename = zip_path_pattern + current_date.strftime('%y%m%d') + '.zip'
        geojson_filenames = ['emergency_restored_section.geojson', 'json/emergency_restored_section.geojson']
        if not os.path.exists(zip_filename):
            print(f"ZIP file does not exist for {current_date.strftime('%Y%m%d')}")
            current_date += timedelta(days=1)
            continue

        with zipfile.ZipFile(zip_filename, 'r') as z:
            for filename in geojson_filenames:
                try:
                    z.extract(filename, output_folder_geojson)
                    extracted_path = os.path.join(output_folder_geojson, filename)
                    break
                except KeyError:
                    continue
            else:
                print(f'No valid GeoJSON file found for {current_date.strftime("%Y%m%d")}')
                current_date += timedelta(days=1)
                continue

        gdf = gpd.read_file(extracted_path)
        fig, ax = plt.subplots(figsize=(10, 10))
        gdf.plot(ax=ax)
        ax.set_xlim([136.6, 137.4])
        ax.set_ylim([36.7, 37.6])
        plot_filename = os.path.join(output_folder_images, f'plot_{current_date.strftime("%Y%m%d")}.png')
        plt.savefig(plot_filename)
        plt.close()

        filtered_geojson_path = os.path.join(output_folder_geojson, f'{current_date.strftime("%Y%m%d")}.geojson')
        gdf.to_file(filtered_geojson_path, driver='GeoJSON')
        current_date += timedelta(days=1)

def create_mp4_from_plots(start_date, end_date, plot_folder, video_output_path):
    start_date = datetime.strptime(start_date, "%Y%m%d")
    end_date = datetime.strptime(end_date, "%Y%m%d")

    image_files = []
    dates = []  # 日付を保持するリスト
    current_date = start_date
    while current_date <= end_date:
        plot_filename = os.path.join(plot_folder, f'plot_{current_date.strftime("%Y%m%d")}.png')
        if os.path.exists(plot_filename):
            image_files.append(plot_filename)
            dates.append(current_date.strftime("%Y-%m-%d"))  # 日付を追加
        current_date += timedelta(days=1)

    if not image_files:
        print("No images found. Exiting...")
        return

    fig, ax = plt.subplots()

    initial_image = mpimg.imread(image_files[0])
    im = ax.imshow(initial_image)
    txt = ax.text(0.5, 0.01, dates[0], color='white', fontsize=12, ha='center', va='center', transform=ax.transAxes, backgroundcolor='black')
    ax.axis('off')  # 軸を非表示にする

    def update(frame):
        img = mpimg.imread(image_files[frame])
        im.set_data(img)
        txt.set_text(dates[frame])  # 日付のテキストを更新
        return im, txt 

    ani = FuncAnimation(fig, update, frames=len(image_files), blit=True)
    ani.save(video_output_path, writer='ffmpeg', fps=1, dpi=300)

    print(f"Video created at {video_output_path}")
    plt.close()

# 以下実行コード

# MLITウェブサイトからデータをダウンロード
download_folder = os.path.join(base_folder, "download_zip_data")
url_pattern = "https://www.mlit.go.jp/road/r6noto/{0}data.zip"
download_zip_files(start_date, end_date, url_pattern, download_folder)

# GeoJSON抽出とプロット
geojson_input_folder = os.path.join(download_folder, 'data_')
output_folder_geojson = os.path.join(base_folder, "extract_geojson")
output_folder_images = os.path.join(base_folder, "output_images")
extract_and_plot_geojson(start_date, end_date, geojson_input_folder, output_folder_geojson, output_folder_images)

# GIF生成
output_folder_images = os.path.join(base_folder, "output_images")
video_output_path = os.path.join(base_folder, "output_animation.mp4")
create_mp4_from_plots("20240112", "20240520", output_folder_images, video_output_path)
