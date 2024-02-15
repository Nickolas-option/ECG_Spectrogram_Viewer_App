import io
import os
from pathlib import Path
from tkinter import OptionMenu, Toplevel, StringVar, BooleanVar
from tkinter import filedialog

import customtkinter
import matplotlib.pyplot as plt
import numpy as np
import wfdb
from PIL import Image
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy import signal
from scipy.signal import spectrogram

# Set the appearance mode and color theme
customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")


class SimpleApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("ECG Viewer")

        self.geometry(f"{1400}x{900}")

        self.record_name = None
        self.record = None
        self.qrs_indices = None


        self.record_folder = None
        self.selected_patient_number = None

        self.lead_number = 0  # Default lead number

        self.first_second_default = 11495
        self.last_second_default = 11500

        self.first_second_var = customtkinter.StringVar(self, value=str(self.first_second_default))
        self.last_second_var = customtkinter.StringVar(self, value=str(self.last_second_default))

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()

        self.fig_spectrogram, self.ax_spectrogram = plt.subplots()
        self.canvas_spectrogram = FigureCanvasTkAgg(self.fig_spectrogram, master=self)
        self.canvas_widget_spectrogram = self.canvas_spectrogram.get_tk_widget()

        self.configure_grid()

        self.entry_widgets = self.create_entry_widgets()
        self.update_button, self.default_button, self.patient_folder_button = self.create_buttons()

        self.canvas_visible = BooleanVar(value=True)

        self.place_widgets()

        self.update_plots()

    def choose_patient_folder(self):
        folder_path = filedialog.askdirectory(title="Select Patient Folder", initialdir=os.getcwd())
        if folder_path:
            self.record_folder = folder_path
            self.update_plots()

    def choose_patient_number(self):
        if not self.record_folder:
            # If the folder is not selected, prompt the user to choose the folder first
            self.choose_patient_folder()
        else:
            hea_files = [f for f in os.listdir(self.record_folder) if f.endswith('.dat')]
            if hea_files:
                # Create a Toplevel window for choosing the patient file
                choose_file_window = Toplevel(self)

                # Variable to store the selected file number
                selected_number_var = StringVar(choose_file_window)
                selected_number_var.set("100")  # Set default value

                # Extract numbers from .hea filenames and sort them
                file_numbers = sorted([int(file.split('.')[0]) for file in hea_files])

                # Create an OptionMenu with file_numbers as options
                file_menu = OptionMenu(choose_file_window, selected_number_var, *file_numbers)
                file_menu.pack()

                def confirm_selection():
                    selected_number = selected_number_var.get()
                    if selected_number:
                        self.record_name = os.path.join(self.record_folder, f'{selected_number}.dat')
                        self.selected_patient_number = int(selected_number)
                        self.update_plots(int(selected_number))
                        choose_file_window.destroy()

                # Add a button to confirm the selection
                confirm_button = customtkinter.CTkButton(choose_file_window, text="OK", command=confirm_selection)
                confirm_button.pack()

                # Center the window on the screen
                choose_file_window.geometry(
                    "+%d+%d" % (self.winfo_screenwidth() / 2 - 100, self.winfo_screenheight() / 2 - 50))

                choose_file_window.mainloop()

    def configure_grid(self):
        for i in range(3, 10):
            self.columnconfigure(i, weight=1)
        for i in range(0,10):
            self.rowconfigure(i, weight=1)

        # Set a fixed width for the columns containing the plots
        self.columnconfigure(3, minsize=400)
        self.columnconfigure(4, minsize=400)

    def create_entry_widgets(self):
        # Create entry widgets for first and last seconds
        first_entry = customtkinter.CTkEntry(self, textvariable=self.first_second_var, width=5, justify="right")
        last_entry = customtkinter.CTkEntry(self, textvariable=self.last_second_var, width=5, justify="right")

        # Set the sticky option to align text to the right
        first_entry.grid(row=1, column=1, padx=(0, 2), pady=(5, 0), sticky="ew")
        last_entry.grid(row=2, column=1, padx=(0, 2), pady=(5, 0), sticky="ew")

        # Create labels for displaying the time for the first and last seconds
        self.first_time_label = customtkinter.CTkLabel(self, text="", width=5)
        self.last_time_label = customtkinter.CTkLabel(self, text="", width=5)

        # Bind the update_time_labels function to the entry fields
        first_entry.bind("<KeyRelease>", self.update_time_labels)
        last_entry.bind("<KeyRelease>", self.update_time_labels)

        # Return the entry widgets
        return first_entry, last_entry

    def update_time_labels(self, event):
        first_seconds = int(self.first_second_var.get())
        last_seconds = int(self.last_second_var.get())

        # Calculate and update the time for the first seconds
        first_hours, first_remainder = divmod(first_seconds, 3600)
        first_minutes, first_seconds = divmod(first_remainder, 60)
        self.first_time_label.configure(
            text=f"First Time: {first_hours} hours, {first_minutes} minutes, {first_seconds} seconds")

        # Calculate and update the time for the last seconds
        last_hours, last_remainder = divmod(last_seconds, 3600)
        last_minutes, last_seconds = divmod(last_remainder, 60)
        self.last_time_label.configure(
            text=f"Last Time: {last_hours} hours, {last_minutes} minutes, {last_seconds} seconds")

    def create_buttons(self):
        return (
            customtkinter.CTkButton(self, text="Update", command=self.update_plots),
            customtkinter.CTkButton(self, text="Default", command=self.set_default_values),
            customtkinter.CTkButton(self, text="Choose Patient Folder", command=self.choose_patient_folder)
        )

    def toggle_canvas(self):
        self.canvas_visible.set(not self.canvas_visible.get())
        self.update_canvas_visibility()

    def update_canvas_visibility(self):
        if self.canvas_visible.get():
            self.canvas_widget.grid_forget()
            self.canvas_widget_spectrogram.grid_forget()
            self.canvas_widget_spectrogram.grid(row=0, column=3, columnspan=5, rowspan=10, pady=5, sticky="nsew")

        else:
            self.canvas_widget.grid(row=6, column=3, columnspan=5, rowspan=8, pady=5, sticky="nsew")
            self.canvas_widget_spectrogram.grid(row=0, column=3, columnspan=5, rowspan=2, pady=5, sticky="nsew")



    def place_widgets(self):
        # Labels for first and last second
        customtkinter.CTkLabel(self, text="start in seconds").grid(row=1, column=1, padx=(10, 0), pady=(5, 0), sticky="w")
        customtkinter.CTkLabel(self, text="finish in seconds").grid(row=2, column=1, padx=(10, 0), pady=(5, 0), sticky="w")

        self.entry_widgets[0].grid(row=1, column=0, padx=(0, 2), pady=(5, 0), sticky="ew")
        self.entry_widgets[1].grid(row=2, column=0, padx=(0, 2), pady=(5, 0), sticky="ew")

        # Choose lead
        choose_lead_button = customtkinter.CTkButton(self, text="Choose Lead", command=self.choose_lead)
        choose_lead_button.grid(row=8, column=1, padx=(0, 2), pady=(5, 0), sticky="e")

        # Time labels
        self.first_time_label.grid(row=4, column=0, columnspan=3, padx=(10, 0), pady=(5, 0), sticky="w")
        self.last_time_label.grid(row=5, column=0, columnspan=3, padx=(10, 0), pady=(5, 0), sticky="w")

        # Buttons for update, default, and patient folder
        self.update_button.grid(row=0, column=0, padx=(0, 2), pady=(5, 0), sticky="e")
        self.default_button.grid(row=0, column=1, padx=(0, 2), pady=(5, 0), sticky="e")

        # Plots for data and spectrogram
        self.canvas_widget.grid(row=6, column=3, columnspan=5, rowspan=8, pady=5, sticky="nsew")
        self.canvas_widget_spectrogram.grid(row=0, column=3, columnspan=5, rowspan=2, pady=5, sticky="nsew")

        # Button to choose patient
        choose_number_button = customtkinter.CTkButton(self, text="Choose Patient", command=self.choose_patient_number)
        choose_number_button.grid(row=6, column=1, padx=(0, 2), pady=(5, 0), sticky="e")

        # Button to download spectrogram
        download_button = customtkinter.CTkButton(self, text="Download Spectrogram", command=self.download_spectrogram)

        download_button.grid(row=7, column=0, padx=(5, 2), pady=(5, 0), sticky="e")

        toggle_canvas_button = customtkinter.CTkButton(self, text="Toggle Canvas", command=self.toggle_canvas)
        toggle_canvas_button.grid(row=7, column=1, padx=(0, 2), pady=(5, 0), sticky="e")

        # Button for patient folder
        self.patient_folder_button.grid(row=6, column=0, padx=(0, 2), pady=(5, 0), sticky="e")

        # # Configure grid weights for rows and columns
        # for i in range(18):
        #     self.rowconfigure(i, weight=1)
        #
        # for j in range(16):
        #     self.columnconfigure(j, weight=1)

    def set_default_values(self):
        self.first_second_var.set(str(self.first_second_default))
        self.last_second_var.set(str(self.last_second_default))

    def choose_lead(self):
        lead_numbers = [str(i + 1) for i in range(self.record.p_signal.shape[1])]
        lead_number_window = Toplevel(self)

        # Variable to store the selected lead number
        selected_lead_var = StringVar(lead_number_window)
        selected_lead_var.set(str(self.lead_number + 1))  # Set default value

        # Create a list of lead numbers (1 to leads_num)

        # Create an OptionMenu with lead_numbers as options
        lead_menu = OptionMenu(lead_number_window, selected_lead_var, *lead_numbers)
        lead_menu.pack()

        def confirm_selection():
            selected_lead = selected_lead_var.get()
            if selected_lead:
                self.lead_number = int(selected_lead) - 1  # Adjust to 0-based index
                self.update_plots()
                lead_number_window.destroy()

        # Add a button to confirm the selection
        confirm_button = customtkinter.CTkButton(lead_number_window, text="OK", command=confirm_selection)
        confirm_button.pack()

        # Center the window on the screen
        lead_number_window.geometry(
            "+%d+%d" % (self.winfo_screenwidth() / 2 - 100, self.winfo_screenheight() / 2 - 50))

        lead_number_window.mainloop()

    def download_spectrogram(self):
        if self.record_name:
            first_second = int(self.first_second_var.get())
            last_second = int(self.last_second_var.get())
            first_sample = int(first_second * self.record.fs)
            last_sample = int(last_second * self.record.fs)

            _, _, Sxx = signal.spectrogram(self.record.p_signal[first_sample:last_sample, 0], self.record.fs,
                                           nperseg=min(len(self.record.p_signal[first_sample:last_sample, 0]), 256),
                                           scaling='spectrum')

            # Create a PIL Image from the spectrogram plot
            fig, ax = plt.subplots()
            ax.pcolormesh(np.linspace(first_second, last_second, len(Sxx[0])),
                          np.linspace(0, self.record.fs / 2, len(Sxx)),
                          np.log10(Sxx))
            ax.set_ylabel('Frequency [Hz]')
            ax.set_xlabel('Time [s]')

            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0.1, dpi=500)
            buffer.seek(0)

            # Use filedialog to get the save path
            folder_name = Path(self.record_folder).name if self.record_folder else "Unknown_Folder"
            default_name = f"ecg-spectrogram-{folder_name}-{self.selected_patient_number}-{self.lead_number}.png"
            file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")],
                                                     initialfile=default_name)

            if file_path:
                # Save the PIL Image to the specified file
                image = Image.open(buffer)
                image.save(file_path)

            buffer.close()
            plt.close()

    def update_plots(self, patient_number=None):
        if patient_number is not None:
            self.record_name = os.path.join(self.record_folder, f'{patient_number}')

        if self.record_name:
            self.record = wfdb.rdrecord(self.record_name)

            qrs_annotations = wfdb.rdann(self.record_name, extension='qrs')
            self.qrs_indices = qrs_annotations.sample

            first_second = int(self.first_second_var.get())
            last_second = int(self.last_second_var.get())

            first_sample = int(first_second * self.record.fs)
            last_sample = int(last_second * self.record.fs)

            # Calculate the time duration
            time_duration = last_second - first_second

            # Calculate the downsampling factor based on the time duration
            self.downsample_factor = max(1, int(time_duration))  # Adjust as needed

            # Downsample the ECG signal
            downsampled_signal = signal.resample(self.record.p_signal[first_sample:last_sample, self.lead_number],
                                                 int(len(self.record.p_signal[first_sample:last_sample,
                                                         0]) / self.downsample_factor))

            downsampled_time = np.linspace(first_second, last_second, len(downsampled_signal))

            # Update the ECG plot with downsampled signal
            self.ax.clear()
            self.ax.plot(downsampled_time, downsampled_signal, label=f'ECG Lead {self.lead_number + 1}')

            self.ax.set_title(f"ECG Viewer ({first_second} to {last_second} Seconds)")
            self.ax.set_xlabel('Time [s]')
            self.ax.set_ylabel('Amplitude')
            self.ax.legend()
            self.canvas.draw()

            frequencies, times, Spectogram = spectrogram(
                self.record.p_signal[first_sample:last_sample, self.lead_number],
                fs=self.record.fs, nperseg=self.record.fs)

            self.ax_spectrogram.clear()
            self.ax_spectrogram.pcolormesh(times, frequencies, 10 * np.log10(Spectogram))
            self.ax_spectrogram.set_ylabel('Frequency [Hz]')
            self.ax_spectrogram.set_xlabel('Time [s]')
            self.canvas_spectrogram.draw()


if __name__ == "__main__":
    app = SimpleApp()
    app.mainloop()
