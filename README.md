# ECG_Spectrogram_Viewer_App
Для изучения спектрограммы необходимо иметь интерактивный Python инструмент, позволяющий выбрать канал ЭКГ и отображать одновременно спектрограмму и саму ЭКГ (выбранный канал).  


## Параметры ввода   

- Время начала отрезка в сек (пересчитывается в чч:мм:сс снизу под полем)  
- Время завершения отрезка в сек (пересчитывается в чч:мм:сс снизу под полем)    
- Выбор папки с ЭКГ   
- Выбор канала из 12   

## Установка   

Для установки программы выполните следующие шаги:   

- Скачайте репозиторий ECG_Spectrogram_Viewer_App   
- Запустите программу main.exe (работает для систем Windows 10/11)
- Запустите команду pip install -r requirements.txt, а затем выполните python main.py (работает для остальных систем) 

## Использование   

- Откройте программу и выберите папку с ЭКГ - "ecg_files — copy"  
- Выберите канал ЭКГ из списка доступных   
- Введите время начала и конца отрезка в сек    
- Нажмите на кнопку "Отобразить" для отображения спектрограммы и ЭКГ   

## Лицензия   

Программа лицензируется под лицензией MIT.
