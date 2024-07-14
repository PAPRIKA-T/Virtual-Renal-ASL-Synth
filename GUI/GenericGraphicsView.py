import os.path
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (QGraphicsView, QLabel, QHBoxLayout, QVBoxLayout, QGraphicsPixmapItem)
from Model.NiiLoader import NiiLoader
from PyQt6.QtCore import Qt, QPointF
from Core.Macros import AnatomicalPlane, array_to_qpixmap
from GUI.GenericGraphicsScene import GenericGraphicsScene
from Core.Macros import get_magnitude


class GenericGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super(GenericGraphicsView, self).__init__(parent)
        self.setAcceptDrops(True)
        self.__nii_loader = None
        self.__status_label_default = None
        self.__status_label = None
        self.focus_plane = AnatomicalPlane.CORONAL  # 选择冠状面
        self.__init_graphics_scene()
        self.__init_toolbar()
        self.__init_statusbar()
        self.__init_main_layout()
        self.__init_graphics_pixmap()

        self.mouse_pressed_pos = None
        self.mouse_present_pos = None
        self.mainwindow = None

        self.view_name = None

    def __init_graphics_scene(self):
        self.__scene = GenericGraphicsScene()
        self.setScene(self.__scene)

    def __init_graphics_pixmap(self):
        self.__pixmap_item = QGraphicsPixmapItem(None)
        self.__scene.addItem(self.__pixmap_item)
        # self.__pixmap_item.setFlags(
        #     QGraphicsPixmapItem.GraphicsItemFlag.ItemIsSelectable |
        #     QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable
        # )

    def __init_toolbar(self):
        self.__bar_layout = QHBoxLayout()
        self.__title_label = QLabel('')
        self.__title_label.setObjectName('GraphicsViewTextItem_TitleLabel')
        self.__title_label.setAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.__rt_label = QLabel('')
        self.__rt_label.setObjectName('GraphicsViewTextItem_RtLabel')
        self.__rt_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.__img_window_width_text = 'WW:0\n'
        self.__img_window_level_text = 'WL:0\n'
        self.__img_index_text = '0/0'
        self.__update_rt_label()

        self.__bar_layout.addWidget(self.__title_label)
        self.__bar_layout.addStretch()
        self.__bar_layout.addWidget(self.__rt_label)
        self.__bar_layout.setContentsMargins(5, 5, 5, 5)

    def __init_statusbar(self):
        self.__status_layout = QHBoxLayout()
        self.__status_label_default = 'No Image Load!'
        self.__status_label = QLabel(self.__status_label_default)
        self.__status_label.setObjectName('GraphicsViewTextItem_PathLabel')
        # self.__path_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.__status_layout.addStretch()
        self.__status_layout.addWidget(self.__status_label)
        self.__status_layout.setContentsMargins(5, 5, 5, 5)

    def __init_main_layout(self):
        self.__main_layout = QVBoxLayout(self)
        self.__main_layout.addLayout(self.__bar_layout)
        self.__main_layout.setSpacing(0)
        self.__main_layout.setContentsMargins(0, 0, 0, 0)
        self.__main_layout.addStretch()
        self.__main_layout.addLayout(self.__status_layout)

    def __update_graphics_pixmap(self, image_array, reset=False):
        if reset:
            self.__pixmap_item.setPixmap(QPixmap())  # 清空 pixmap
            return
        if self.__nii_loader is None:
            print('GenericGraphicsView::__update_graphics_pixmap():nii_loader is None')
            return
        self.__pixmap_item.setPixmap(array_to_qpixmap(image_array))
        self.fitInView(self.__pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)  # 保持宽高比
        # print('GenericGraphicsView::__update_graphics_pixmap():update pixmap successfully')
        # size = self.__pixmap_item.pixmap().size()
        # print(f"图片大小为: {size.width()} x {size.height()}")

    def __update_img_index_label(self, index, reset=False):
        if reset:
            text = "{}/{}".format(0, 0)
        else:
            dim = self.__nii_loader.get_plane_dim(self.focus_plane)
            text = "{}/{}".format(index+1, dim)
        self.__img_index_text = text
        self.__update_rt_label()

    def __update_rt_label(self):
        self.__rt_label.setText(self.__img_window_width_text +
                                self.__img_window_level_text +
                                self.__img_index_text)

    def __update_window_label(self, ww, wl, reset=False):
        if reset:
            self.__img_window_width_text = f'WW:0\n'
            self.__img_window_level_text = f'WL:0\n'
        else:
            self.__img_window_width_text = f'WW:{ww:.2f}\n'
            self.__img_window_level_text = f'WL:{wl:.2f}\n'
        self.__update_rt_label()

    """
    override event function
    """
    def resizeEvent(self, event):
        super(GenericGraphicsView, self).resizeEvent(event)
        if self.__nii_loader is None:
            return
        self.fitInView(self.__pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)  # 保持宽高比

    def wheelEvent(self, event):
        if self.__nii_loader is None:
            print('GenericGraphicsView::wheelEvent():nii_loader is None')
            return
        current_index = self.__nii_loader.get_plane_current_index(self.focus_plane)
        if event.angleDelta().y() > 0:
            current_index -= 1
        else:
            current_index += 1
        try:
            self.__nii_loader.set_plane_current_index(self.focus_plane, current_index)
            image_array = self.__nii_loader.get_plane_slice(self.focus_plane, current_index)
            self.__update_graphics_pixmap(image_array)
            self.__update_img_index_label(current_index)
        except ValueError as e:
            print(e)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.accept()  # 强制接受拖放事件

    def dropEvent(self, event):
        if self.mainwindow != None:
            if self.view_name != 'ASL Super':
                if self.mainwindow.ASL_Infer_GraphicsView.isLoadNiiData():
                    self.mainwindow.msg_box.show_and_wait()
                    if self.mainwindow.msg_box.clicked_button == self.mainwindow.msg_box.NOT_YET:
                        return

        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            print(file_path)
            if file_path.endswith('.nii') or file_path.endswith('.nii.gz'):
                self.read_nii_data(file_path)
                event.acceptProposedAction()

                if self.mainwindow != None:
                    self.mainwindow.eva_change_when_update_ASL()

                return
        event.ignore()

    def mousePressEvent(self, event):
        self.mouse_present_pos = event.pos()
        self.mouse_pressed_pos = event.pos()
        # print(f"mouse_pressed_pos: {self.mouse_present_pos}")

    def mouseMoveEvent(self, event):
        if self.__nii_loader is None:
            return
        if event.buttons () == Qt.MouseButton.LeftButton:
            delta_x = event.pos().x() - self.mouse_present_pos.x()
            delta_y = event.pos().y() - self.mouse_present_pos.y()
            self.__nii_loader.set_window_width(self.__nii_loader.get_window_width()
                                               + delta_x*self.__nii_loader.get_ww_adjust_interval())
            self.__nii_loader.set_window_level(self.__nii_loader.get_window_level()
                                               + delta_y*self.__nii_loader.get_ww_adjust_interval())
            self.__update_window_label(self.__nii_loader.get_window_width(),
                                       self.__nii_loader.get_window_level())

            current_index = self.__nii_loader.get_plane_current_index(self.focus_plane)
            image_array = self.__nii_loader.get_plane_slice(self.focus_plane, current_index)
            self.__update_graphics_pixmap(image_array)
        elif event.buttons() == Qt.MouseButton.RightButton:
            pass
        elif event.buttons() == Qt.MouseButton.LeftButton:
            pass
            # delta = event.pos() - self.mouse_present_pos
            # new_pos = self.__pixmap_item.scenePos() + delta.toPointF()
            # self.__pixmap_item.setPos(new_pos)
        self.mouse_present_pos = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_pressed_pos = QPointF()

    """
    public function
    """
    def set_title_label_text(self, text):
        self.__title_label.setText(text)

    def set_title_label_objectname(self, n):
        self.__title_label.setObjectName(n)

    def update_status_label(self, path, reset=False):
        if reset:
            self.__status_label.setText(self.__status_label_default)
        else:
            self.__status_label.setText(path)

    def set_status_label_default(self, t):
        self.__status_label_default = t

    def get_status_label(self):
        return self.__status_label.text()

    def read_nii_data(self, file_path):
        self.__nii_loader = NiiLoader(file_path)
        current_index = self.__nii_loader.get_plane_current_index(self.focus_plane)
        try:
            image_array = self.__nii_loader.get_plane_slice(self.focus_plane, current_index)
            self.__update_graphics_pixmap(image_array)

            parent_dir = os.path.basename(os.path.dirname(file_path))
            file_name = os.path.basename(file_path)
            self.update_status_label(os.path.join(parent_dir, file_name))

            self.__update_img_index_label(current_index)
            self.__update_window_label(self.__nii_loader.get_window_width(),
                                       self.__nii_loader.get_window_level())
        except ValueError as e:
            print(e)

    def resetGraphicsView(self):
        self.update_status_label([], reset=True)
        self.__update_img_index_label([], reset=True)
        self.__update_window_label([], [], reset=True)
        self.__update_graphics_pixmap([], reset=True)
        self.__nii_loader = None

    def isLoadNiiData(self):
        if self.__nii_loader is None:
            return False
        else:
            return True

    def save_nii_file(self, save_path):
        if self.__nii_loader is None:
            print('GenericGraphicsView::save_nii_file():nii_loader is None')
            return
        self.__nii_loader.save_nii_file(save_path)
