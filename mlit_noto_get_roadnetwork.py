import requests
import os
import zipfile
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import imageio
import numpy as np
from datetime import datetime, timedelta

# 共通のベースフォルダ．データ期間の設定，MILIウェブサイトのURL指定
base_folder = "/Users/makoto/Dropbox/00_git/202401_Noto_IP_team"
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

def extract_and_plot_geojson(start_date, end_date, zip_path_pattern, output_folder):
    current_date = datetime.strptime(start_date, "%Y%m%d")
    end_date = datetime.strptime(end_date, "%Y%m%d")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

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
                    z.extract(filename, output_folder)
                    extracted_path = os.path.join(output_folder, filename)
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
        plot_filename = os.path.join(output_folder, f'plot_{current_date.strftime("%Y%m%d")}.png')
        plt.savefig(plot_filename)
        plt.close()

        filtered_geojson_path = os.path.join(output_folder, f'{current_date.strftime("%Y%m%d")}.geojson')
        gdf.to_file(filtered_geojson_path, driver='GeoJSON')
        current_date += timedelta(days=1)

def create_gif_from_plots(start_date, end_date, plot_folder, gif_output_path):
    # 文字列から datetime オブジェクトに変換
    start_date = datetime.strptime(start_date, "%Y%m%d")
    end_date = datetime.strptime(end_date, "%Y%m%d")

    # PNGファイルのリストを作成
    png_files = []
    current_date = start_date
    while current_date <= end_date:
        plot_filename = os.path.join(plot_folder, f'plot_{current_date.strftime("%Y%m%d")}.png')
        if os.path.exists(plot_filename):
            png_files.append((plot_filename, current_date.strftime("%Y-%m-%d")))
        current_date += timedelta(days=1)

    # GIFファイルを作成
    with imageio.get_writer(gif_output_path, mode='I', duration=1.0) as writer:
        for filename, date in png_files:
            # 画像を読み込む
            image = mpimg.imread(filename)
            fig, ax = plt.subplots(dpi=300)  # DPIを設定
            ax.imshow(image)
            # 日付を追加
            ax.text(136.7, 37.55, date, color='white', fontsize=12, ha='center', va='center', backgroundcolor='black')
            ax.axis('off')  # 軸と枠を非表示に

            # プロットを画像データに変換してGIFに追加
            fig.canvas.draw()
            image_from_plot = np.frombuffer(fig.canvas.tostring_rgb(), dtype='uint8')
            image_from_plot = image_from_plot.reshape(fig.canvas.get_width_height()[::-1] + (3,))
            writer.append_data(image_from_plot)
            
            plt.close()

    print(f"GIF created at {gif_output_path}")

# 以下実行コード

# MLITウェブサイトからデータをダウンロード
download_folder = os.path.join(base_folder, "MLIT_disrup_data")
url_pattern = "https://www.mlit.go.jp/road/r6noto/{0}data.zip"
download_zip_files(start_date, end_date, url_pattern, download_folder)

# GeoJSON抽出とプロット
geojson_input_folder = os.path.join(download_folder, 'data_')
output_folder_geojson = os.path.join(base_folder, "tentative_output_geojson")
extract_and_plot_geojson(start_date, end_date, geojson_input_folder, output_folder_geojson)

# GIF生成
output_folder_gif = os.path.join(base_folder, "tentative_output")
gif_output_path = os.path.join(base_folder, "output_animation.gif")
create_gif_from_plots(start_date, end_date, output_folder_gif, gif_output_path)
