from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QHBoxLayout, QFileDialog, QFormLayout, QLabel, QGroupBox,QMessageBox
from GUI.GenericGraphicsView import GenericGraphicsView
from GUI.GenericButton import GenericButton
from PyQt6.QtCore import pyqtSlot
import os.path
from PyQt6.QtCore import QTimer
from Core.Macros import search_files
from Core.Macros import search_excel_column
from Core.Macros import read_excel_row_values
from Core.Macros import VRAS_config

class MessageBox(QMessageBox):
    def __init__(self,mainwindow):
        super().__init__()
        self.mainwindow = mainwindow
        self.setWindowTitle("Confirmation")
        self.setText("Inferred image existed, delete all images and start a new one?")
        self.setStandardButtons(QMessageBox.StandardButton.NoButton)  # Remove standard buttons
        self.delete_all_button = self.addButton("Delete all", QMessageBox.ButtonRole.YesRole)
        self.not_yet_button = self.addButton("Not yet", QMessageBox.ButtonRole.NoRole)

        self.DELETE_ALL = 2
        self.NOT_YET = 3

    def show_and_wait(self):
        self.clicked_button = self.exec()
        if self.clicked_button == self.DELETE_ALL: # 点击delete all的时候,这个值被置为2
            print("delete_all_button clicked")
            self.mainwindow.on_img_del_btn_clicked()
        elif self.clicked_button == self.NOT_YET:
            print("Not yet button clicked")
        else:
            print("Unknown button clicked:", self.clicked_button)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('VRAS(Virtual Renal ASL Synth)')
        self.setWindowIcon(QIcon(VRAS_config.WindowICON))

        self.__init_graphics_view()
        self.__init_btn()
        self.__init_right_bottom_layout()
        self.__init_right_bottom_h_layout()

        self.__init_right_layout()
        self.__init_main_layout()
        self.__init_slots()

        self.predict_timer = QTimer(self)
        self.predict_timer.setSingleShot(True)
        self.predict_timer.timeout.connect(self.__on_predict_timeout)
        self.is_inferred = False

        self.msg_box = MessageBox(self)

    def __init_main_layout(self):
        self.__main_layout = QHBoxLayout(self)
        self.__main_layout.setContentsMargins(0, 0, 0, 0)
        self.__main_layout.setSpacing(0)
        self.__main_layout.addLayout(self.__view_layout)
        self.__main_layout.addLayout(self.__right_layout)
        self.__main_layout.setStretch(0, 7)
        self.__main_layout.setStretch(1, 3)

    def __init_graphics_view(self):
        self.__view_layout = QGridLayout()

        self.T1_GraphicsView = GenericGraphicsView(self)
        self.T1_GraphicsView.set_title_label_text('T1')
        self.T2_GraphicsView = GenericGraphicsView(self)
        self.T2_GraphicsView.set_title_label_text('T2')
        self.DWI_GraphicsView = GenericGraphicsView(self)
        self.DWI_GraphicsView.set_title_label_text('DWI')
        self.ASL_Super_GraphicsView = GenericGraphicsView(self)
        self.ASL_Super_GraphicsView.set_title_label_text('ASL Super')

        self.T1_GraphicsView.mainwindow = self
        self.T2_GraphicsView.mainwindow = self
        self.DWI_GraphicsView.mainwindow = self
        self.ASL_Super_GraphicsView.mainwindow = self

        self.T1_GraphicsView.view_name = 'T1'
        self.T2_GraphicsView.view_name = 'T2'
        self.DWI_GraphicsView.view_name = 'DWI'
        self.ASL_Super_GraphicsView.view_name = 'ASL Super'

        self.__view_layout.addWidget(self.T1_GraphicsView, 0, 0)
        self.__view_layout.addWidget(self.T2_GraphicsView, 0, 1)
        self.__view_layout.addWidget(self.DWI_GraphicsView, 1, 0)
        self.__view_layout.addWidget(self.ASL_Super_GraphicsView, 1, 1)
        self.__view_layout.setSpacing(5)
        self.__view_layout.setContentsMargins(5, 5, 5, 5)

    def __init_btn(self):
        self.__btn_layout = QVBoxLayout()

        self.__img_chose_T1_btn = GenericButton(self)
        self.__img_chose_T1_btn.setText('T1')
        self.__img_chose_T2_btn = GenericButton(self)
        self.__img_chose_T2_btn.setText('T2')
        self.__img_chose_DWI_btn = GenericButton(self)
        self.__img_chose_DWI_btn.setText('DWI')
        self.__img_chose_ASL_btn = GenericButton(self)
        self.__img_chose_ASL_btn.setText('ASL')
        self.__img_generate_btn = GenericButton(self)
        self.__img_generate_btn.setText('Infer')
        self.__img_generate_btn.setObjectName('Infer')
        self.__img_save_btn = GenericButton(self)
        self.__img_save_btn.setText('Save')
        self.__img_del_btn = GenericButton(self)
        self.__img_del_btn.setText('Del')

        self.__btn_layout.addWidget(self.__img_chose_T1_btn)
        self.__btn_layout.addWidget(self.__img_chose_T2_btn)
        self.__btn_layout.addWidget(self.__img_chose_DWI_btn)
        self.__btn_layout.addWidget(self.__img_chose_ASL_btn)
        self.__btn_layout.addWidget(self.__img_generate_btn)
        self.__btn_layout.addWidget(self.__img_save_btn)
        self.__btn_layout.addWidget(self.__img_del_btn)
        self.__btn_layout.setContentsMargins(0, 0, 0, 0)
        self.__btn_layout.addStretch()

    def __init_slots(self) -> None:
        self.__img_chose_T1_btn.clicked.connect(self.__on_img_chose_btn_clicked)
        self.__img_chose_T2_btn.clicked.connect(self.__on_img_chose_btn_clicked)
        self.__img_chose_DWI_btn.clicked.connect(self.__on_img_chose_btn_clicked)
        self.__img_chose_ASL_btn.clicked.connect(self.__on_img_chose_btn_clicked)
        self.__img_generate_btn.clicked.connect(self.__on_img_generate_btn_clicked)
        self.__img_save_btn.clicked.connect(self.__on_img_save_btn_clicked)
        self.__img_del_btn.clicked.connect(self.on_img_del_btn_clicked)

    def __init_right_layout(self) -> None:
        self.__right_layout = QVBoxLayout()
        self.ASL_Infer_GraphicsView = GenericGraphicsView(self)
        self.ASL_Infer_GraphicsView.set_title_label_text('ASL_Infer')
        self.ASL_Infer_GraphicsView.set_title_label_objectname('ASL_Infer')
        self.ASL_Infer_GraphicsView.set_status_label_default('No Infer')
        self.ASL_Infer_GraphicsView.update_status_label('No Infer')
        self.ASL_Infer_GraphicsView.setAcceptDrops(False)
        self.__right_layout.addWidget(self.ASL_Infer_GraphicsView)
        self.__right_layout.addSpacing(5)
        self.__right_layout.addLayout(self.__right_bottom_H_layout)
        self.__right_layout.setContentsMargins(0, 5, 5, 5)
        # self.__right_layout.addSpacing(150)

    def __init_right_bottom_h_layout(self) -> None:
        self.__right_bottom_H_layout = QHBoxLayout()
        self.__right_bottom_H_layout.addLayout(self.__btn_layout)
        self.__right_bottom_H_layout.addSpacing(5)
        self.__right_bottom_H_layout.addWidget(self.rb_em_group_box)
        self.__right_bottom_H_layout.setContentsMargins(0, 0, 0, 0)

    def __init_right_bottom_layout(self) -> None:
        self.rb_em_group_box = QGroupBox('Evaluation Metrics')
        self.__rb_g_layout = QGridLayout()

        self.__nrmse_label = QLabel('Null')
        self.__nrmse_label.setObjectName('EvaluationLabel')
        self.__smape_label = QLabel('Null')
        self.__smape_label.setObjectName('EvaluationLabel')
        self.__logac_label = QLabel('Null')
        self.__logac_label.setObjectName('EvaluationLabel')
        self.__medsymac_label = QLabel('Null')
        self.__medsymac_label.setObjectName('EvaluationLabel')
        self.__ssim_label = QLabel('Null')
        self.__ssim_label.setObjectName('EvaluationLabel')

        self.__nrmse_label_t = QLabel('Nrmse')
        self.__nrmse_label_t.setObjectName('EvaluationLabel')
        self.__smape_label_t = QLabel('Smape')
        self.__smape_label_t.setObjectName('EvaluationLabel')
        self.__logac_label_t = QLabel('Logac')
        self.__logac_label_t.setObjectName('EvaluationLabel')
        self.__medsymac_label_t = QLabel('Medsymac')
        self.__medsymac_label_t.setObjectName('EvaluationLabel')
        self.__ssim_label_t = QLabel('SSIM')
        self.__ssim_label_t.setObjectName('EvaluationLabel')

        self.__rb_g_layout.addWidget(self.__nrmse_label_t, 0, 0)
        self.__rb_g_layout.addWidget(self.__nrmse_label, 0, 1)
        self.__rb_g_layout.addWidget(self.__smape_label_t, 1, 0)
        self.__rb_g_layout.addWidget(self.__smape_label, 1, 1)
        self.__rb_g_layout.addWidget(self.__logac_label_t, 2, 0)
        self.__rb_g_layout.addWidget(self.__logac_label, 2, 1)
        self.__rb_g_layout.addWidget(self.__medsymac_label_t, 3, 0)
        self.__rb_g_layout.addWidget(self.__medsymac_label, 3, 1)
        self.__rb_g_layout.addWidget(self.__ssim_label_t, 4, 0)
        self.__rb_g_layout.addWidget(self.__ssim_label, 4, 1)

        self.rb_em_group_box.setLayout(self.__rb_g_layout)

    @pyqtSlot()
    def __on_img_chose_btn_clicked(self):
        file_dialog = QFileDialog(self)
        window_title_list = ['T1', 'T2', 'DWI', 'ASL']
        file_dialog.setWindowTitle('Open NIfTI')  # 设置对话框标题
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)  # 设置为选择文件模式
        file_dialog.setOption(QFileDialog.Option.ShowDirsOnly, False)  # 设置为只显示文件夹
        file_dialog.setOption(QFileDialog.Option.DontUseNativeDialog, False)  # 使用系统原生对话框
        file_dialog.setNameFilter('NIfTI files (*.nii *.nii.gz)')
        if file_dialog.exec():
            selected_filepath = file_dialog.selectedFiles()[0]
            # print(f"selected_filepath: {selected_filepath}")

            if self.sender() == self.__img_chose_T1_btn:
                if self.ASL_Infer_GraphicsView.isLoadNiiData():
                    self.msg_box.show_and_wait()
                    if self.msg_box.clicked_button == self.msg_box.NOT_YET:
                        return
                self.T1_GraphicsView.read_nii_data(selected_filepath)

            elif self.sender() == self.__img_chose_T2_btn:
                if self.ASL_Infer_GraphicsView.isLoadNiiData():
                    self.msg_box.show_and_wait()
                    if self.msg_box.clicked_button == self.msg_box.NOT_YET:
                        return
                self.T2_GraphicsView.read_nii_data(selected_filepath)

            elif self.sender() == self.__img_chose_DWI_btn:
                if self.ASL_Infer_GraphicsView.isLoadNiiData():
                    self.msg_box.show_and_wait()
                    if self.msg_box.clicked_button == self.msg_box.NOT_YET:
                        return
                self.DWI_GraphicsView.read_nii_data(selected_filepath)

            elif self.sender() == self.__img_chose_ASL_btn:
                self.ASL_Super_GraphicsView.read_nii_data(selected_filepath)
                self.eva_change_when_update_ASL()
            else:
                return

    def __on_img_generate_btn_clicked(self):
        if self.is_inferred:
            # print('MainWindow::__on_img_generate_btn_clicked():had inferred')
            # return

            self.msg_box.show_and_wait()
            if self.msg_box.clicked_button == self.msg_box.NOT_YET:
                return

        if self.T1_GraphicsView.isLoadNiiData() and self.T2_GraphicsView.isLoadNiiData() \
                and self.DWI_GraphicsView.isLoadNiiData():
                # and self.__ASL_Super_GraphicsView.isLoadNiiData():
            self.ASL_Infer_GraphicsView.update_status_label('Inferring...')
            self.predict_timer.start(VRAS_config.PredInterval)

    def __on_predict_timeout(self):
        file_path = self.T1_GraphicsView.get_status_label()
        parent_dir = os.path.basename(os.path.dirname(file_path))

        # update View
        directory = VRAS_config.PredNiiDir
        search_string = parent_dir
        matched_files = search_files(directory, search_string)
        print(f"Files containing '{search_string}':")
        for file in matched_files:
            print(file)
        self.ASL_Infer_GraphicsView.read_nii_data(matched_files[0])
        self.ASL_Infer_GraphicsView.update_status_label('Inferred Success')
        self.is_inferred = True
        if self.ASL_Super_GraphicsView.isLoadNiiData():
            self.eva_change_when_update_ASL()

    def update_eva_label(self, eva_values, reset=False):
        if reset:
            self.__nrmse_label.setText('Null')
            self.__smape_label.setText('Null')
            self.__logac_label.setText('Null')
            self.__medsymac_label.setText('Null')
            self.__ssim_label.setText('Null')
            return
        self.__nrmse_label.setText(f"{eva_values[0]:.3f}")
        self.__smape_label.setText(f"{eva_values[1]:.3f}")
        self.__logac_label.setText(f"{eva_values[2]:.3f}")
        self.__medsymac_label.setText(f"{eva_values[3]:.3f}")
        self.__ssim_label.setText(f"{eva_values[4]:.3f}")

    def __on_img_save_btn_clicked(self):
        if not self.is_inferred:
            return
        # Open a save file dialog
        save_path = QFileDialog.getSaveFileName(self, "Save NII File",
                                                VRAS_config.PredNiiSaveDir, "NIfTI Files (*.nii.gz)")
        self.ASL_Infer_GraphicsView.save_nii_file(save_path[0])

    def on_img_del_btn_clicked(self):
        # if not self.is_inferred:
        #     return
        self.update_eva_label([], reset=True)
        self.T1_GraphicsView.resetGraphicsView()
        self.T2_GraphicsView.resetGraphicsView()
        self.DWI_GraphicsView.resetGraphicsView()
        self.ASL_Infer_GraphicsView.resetGraphicsView()
        self.ASL_Super_GraphicsView.resetGraphicsView()
        self.is_inferred = False

    def eva_change_when_update_ASL(self):
        if self.T1_GraphicsView.isLoadNiiData() and self.T2_GraphicsView.isLoadNiiData() \
                and self.DWI_GraphicsView.isLoadNiiData() and self.ASL_Infer_GraphicsView.isLoadNiiData():

            file_path = self.ASL_Super_GraphicsView.get_status_label()
            parent_dir = os.path.basename(os.path.dirname(file_path))
            search_string = parent_dir
            # update Evaluation Label
            file_path = VRAS_config.PredExcel
            column = 'A'
            matched_cells = search_excel_column(file_path, column, search_string)
            print(f"Cells in column '{column}' containing '{search_string}':")
            eva_values = []
            for row, value in matched_cells:
                print(f"Row {row}: {value}")
                eva_values.append(read_excel_row_values(file_path, row))
                print(f"Values in row {row}:")
                print(eva_values)

            self.update_eva_label([eva_values[0][1], eva_values[0][2],
                                   eva_values[0][3], eva_values[0][4],
                                   eva_values[0][7]])

