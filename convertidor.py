import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pytube import YouTube, Playlist
from pydub import AudioSegment
import os
import threading

class YouTubeConverterApp:
    def __init__(self, master):
        # Inicialización de la aplicación y configuración de la ventana principal
        self.master = master
        self.master.title("YouTube Converter App")

        # Creación de widgets en la interfaz gráfica
        self.create_widgets()

    def create_widgets(self):
        # Creación de etiquetas, botones, entradas y otros elementos en la interfaz

        # Etiqueta y entrada para la URL de YouTube
        self.label_url = ttk.Label(self.master, text="Ingrese la URL de YouTube:")
        self.label_url.grid(row=0, column=0, padx=10, pady=10, sticky='w')
        self.url_entry = ttk.Entry(self.master, width=50)
        self.url_entry.grid(row=0, column=1, padx=10, pady=10, sticky='w')

        # Botones para pegar URL, limpiar entrada y elegir carpeta de destino
        self.paste_button = ttk.Button(self.master, text="Pegar el Link del video ", command=self.paste_content)
        self.paste_button.grid(row=0, column=2, padx=10, pady=10, sticky='w')
        self.clear_button = ttk.Button(self.master, text="Limpiar", command=self.clear_content)
        self.clear_button.grid(row=0, column=3, padx=10, pady=10, sticky='w')
        self.choose_folder_button = ttk.Button(self.master, text="Elegir Carpeta guardar", command=self.choose_folder)
        self.choose_folder_button.grid(row=1, column=2, padx=10, pady=10, sticky='w')

        # Etiqueta y entrada para la carpeta de destino
        self.label_folder = ttk.Label(self.master, text="Carpeta de Descarga:")
        self.label_folder.grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.folder_path_text = ttk.Entry(self.master, width=50, state='disabled')
        self.folder_path_text.grid(row=1, column=1, padx=10, pady=10, sticky='w')

        # Casillas de verificación para elegir el formato de salida (MP3 o MP4)
        self.mp3_var = tk.BooleanVar()
        self.mp3_checkbox = ttk.Checkbutton(self.master, text="Convertir a MP3", variable=self.mp3_var)
        self.mp3_checkbox.grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.mp4_var = tk.BooleanVar()
        self.mp4_checkbox = ttk.Checkbutton(self.master, text="Convertir a MP4", variable=self.mp4_var)
        self.mp4_checkbox.grid(row=2, column=1, padx=10, pady=10, sticky='w')

        # Botón para iniciar la descarga y conversión
        self.download_button = ttk.Button(self.master, text="Descargar y Convertir ", command=self.download_and_convert)
        self.download_button.grid(row=2, column=2, padx=10, pady=10, sticky='w')

        # Área de texto para mostrar progreso y barra de progreso
        self.progress_text = tk.Text(self.master, height=5, width=115, state='disabled')
        self.progress_text.grid(row=3, column=0, columnspan=5, padx=10, pady=10, sticky='w')
        self.progress_bar = ttk.Progressbar(self.master, orient='horizontal', length=810, mode='determinate')
        self.progress_bar.grid(row=4, column=0, columnspan=5, padx=10, pady=10, sticky='w')

    # Métodos para las acciones de los botones
    def paste_content(self):
        # Pegar el contenido del portapapeles en la entrada de URL
        clipboard_content = self.master.clipboard_get()
        self.url_entry.insert(tk.END, clipboard_content)

    def clear_content(self):
        # Limpiar la entrada de URL
        self.url_entry.delete(0, tk.END)

    def choose_folder(self):
        # Elegir la carpeta de destino
        folder_path = filedialog.askdirectory()
        self.folder_path = folder_path
        self.folder_path_text.config(state='normal')
        self.folder_path_text.delete(0, 'end')
        self.folder_path_text.insert(0, folder_path)
        self.folder_path_text.config(state='disabled')

    def download_and_convert(self):
        # Descargar y convertir el video o la lista de reproducción de YouTube
        youtube_url = self.url_entry.get()

        if not youtube_url:
            messagebox.showwarning("Advertencia", "Por favor, ingrese una URL de YouTube.")
            return

        if not hasattr(self, 'folder_path'):
            messagebox.showwarning("Advertencia", "Por favor, elija una carpeta de destino.")
            return

        try:
            if "playlist" in youtube_url.lower():
                # Descargar lista de reproducción
                playlist = Playlist(youtube_url)
                playlist_folder = os.path.join(self.folder_path, self.sanitize_filename(playlist.title))
                os.makedirs(playlist_folder, exist_ok=True)

                if not os.path.exists(playlist_folder):
                    messagebox.showerror("Error", f"No se pudo crear el directorio: {playlist_folder}")
                    return

                self.update_progress(f"Descargando lista de reproducción: {playlist.title}")

                total_videos = len(playlist.video_urls)

                # Configurar la barra de progreso
                self.progress_bar['value'] = 0
                self.progress_bar['maximum'] = total_videos

                # Iniciar hilo para la descarga y conversión
                thread = threading.Thread(target=self.download_playlist, args=(playlist, playlist_folder, total_videos))
                thread.start()

            else:
                # Descargar video de YouTube
                self.download_video(youtube_url, self.folder_path)

            self.update_progress("Descarga y conversión completadas.")

        except FileNotFoundError:
            messagebox.showerror("Error", "No se encontró el archivo para la conversión.")
        except Exception as e:
            messagebox.showerror("Error", f"Error durante la descarga o conversión: {str(e)}")

    def download_playlist(self, playlist, playlist_folder, total_videos):
        # Descargar videos de una lista de reproducción
        for index, video_url in enumerate(playlist.video_urls):
            try:
                self.download_video(video_url, playlist_folder)
                self.update_progress(f"Video {index + 1}/{total_videos} descargado")

                # Actualizar la barra de progreso
                self.progress_bar['value'] = index + 1
                self.master.update_idletasks()
            except Exception as e:
                self.update_progress(f"Error durante la descarga del video {index + 1}: {str(e)}")

    def download_video(self, video_url, output_folder):
        # Descargar un video de YouTube y realizar conversiones
        try:
            yt = YouTube(video_url)
            self.update_progress(f"Descargando video: {yt.title}")

            # Elegir streams de audio y video
            video_stream = yt.streams.filter(file_extension="mp4", progressive=True).first()

            if video_stream:
                # Descargar el video con audio incorporado
                video_file_path = video_stream.download(output_path=output_folder, filename=f"{yt.title}")

                self.update_progress(f"Video descargado: {yt.title}, comenzando la conversión...")

                # Convertir a MP3
                if self.mp3_var.get():
                    self.convert_to_mp3(video_file_path, os.path.join(output_folder, f"{yt.title}.mp3"))

                # Convertir a MP4
                if self.mp4_var.get():
                    self.convert_to_mp4(video_file_path, os.path.join(output_folder, f"{yt.title}.mp4"))

                self.update_progress(f"Conversión completa para: {yt.title}")

            else:
                self.update_progress(f"No se pudo obtener el stream de video para: {yt.title}")
        except Exception as e:
            self.update_progress(f"Error durante la descarga o conversión: {str(e)}")

    def convert_to_mp3(self, input_file, output_file):
        # Convertir un archivo de video a MP3
        audio = AudioSegment.from_file(input_file, format="mp4")
        audio.export(output_file, format="mp3")
        os.remove(input_file)  # Eliminar el archivo de video después de la conversión

    def convert_to_mp4(self, input_file, output_file):
        # Renombrar un archivo de video como archivo de salida (MP4)
        os.rename(input_file, output_file)

    def sanitize_filename(self, filename):
        # Eliminar caracteres no deseados de un nombre de archivo
        return "".join([c for c in filename if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).rstrip()

    def update_progress(self, message):
        # Actualizar el área de texto de progreso con un nuevo mensaje
        self.progress_text.config(state='normal')
        self.progress_text.insert('end', message + '\n')
        self.progress_text.see('end')
        self.progress_text.config(state='disabled')

    def reset_progress(self):
        # Restablecer el área de texto de progreso y la barra de progreso
        self.progress_text.config(state='normal')
        self.progress_text.delete(1.0, 'end')
        self.progress_text.config(state='disabled')
        self.progress_bar['value'] = 0

def main():
    # Función principal para iniciar la aplicación
    root = tk.Tk()
    app = YouTubeConverterApp(root)
    root.mainloop()

if __name__ == "__main__":
    # Ejecutar la aplicación cuando el script se ejecuta directamente
    main()
