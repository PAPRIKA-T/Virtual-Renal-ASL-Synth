import SimpleITK as sitk
from Core.Macros import AnatomicalPlane
import numpy as np
EPS = 1e-8


class NiiLoader:
    def __init__(self, file_path):
        self.__nii_data = None
        self.__planes_current_index = None
        self.__window_width = None
        self.__window_level = None
        self.__read_nii_data(file_path)

    def __read_nii_data(self, file_path):
        """
        读取nii图像
        :param file_path: nii图像路径
        """
        self.__nii_data = sitk.ReadImage(file_path)
        print('NiiLoader::__read_nii_data():nii_data read successfully')
        image_array = sitk.GetArrayFromImage(self.__nii_data)
        # 获取窗宽和窗位
        min_intensity = np.min(image_array)
        max_intensity = np.max(image_array)
        self.__window_width = max_intensity - min_intensity
        self.__window_level = (max_intensity + min_intensity) / 2
        self.__ww_adjust_interval = (max_intensity - min_intensity)/200
        # print(f"窗宽: {self.__window_width}, 窗位: {self.__window_level}")
        # print(f"min: {min_intensity}, max: {max_intensity}")
        # # 获取头文件信息
        # header = self.__nii_data.GetMetaDataKeys()
        # # 输出头文件信息
        # for key in header:
        #     print(f"{key}: {self.__nii_data.GetMetaData(key)}")

        # print(f"image_array: {image_array.shape[0]} ,"
        #       f" {image_array.shape[1]} ,"
        #       f" {image_array.shape[2]}")
        self.__planes_current_index = {'AXIAL': image_array.shape[1]//2,
                                       'CORONAL': image_array.shape[0]//2,
                                       'SAGITTAL': image_array.shape[2]//2}

    def save_nii_file(self, save_path):
        try:
            sitk.WriteImage(self.__nii_data, save_path)
            print(f"Saved NII file to: {save_path}")
        except Exception as e:
            print(f"Error saving NII file: {e}")

    def get_window_level(self):
        return self.__window_level

    def get_window_width(self):
        return self.__window_width

    def set_window_width(self, window_width):
        self.__window_width = window_width

    def set_window_level(self, window_level):
        self.__window_level = window_level

    def get_ww_adjust_interval(self):
        return self.__ww_adjust_interval

    def get_plane_slice(self, plane, index):
        """
        获取指定索引的冠状位切片
        :param index: 冠状位切片的索引
        :param plane: AnatomicalPlane 枚举，指定解剖面（AXIAL、CORONAL、SAGITTAL）
        :return: 冠状位切片的 numpy 数组
        """
        # 检查是否加载图像数据
        if self.__nii_data is None:
            print('NiiLoader::get_coronal_slice():nii_data is None')
            return None
        # 将图像转换为 numpy 数组
        image_array = sitk.GetArrayFromImage(self.__nii_data)
        # 检查索引是否在有效范围内
        if plane == AnatomicalPlane.AXIAL:
            if index < 0 or index >= image_array.shape[1]:
                raise ValueError("NiiLoader::get_coronal_slice():索引超出范围")
            result_array = image_array[:, index, :]
        elif plane == AnatomicalPlane.CORONAL:
            if index < 0 or index >= image_array.shape[0]:
                raise ValueError("NiiLoader::get_coronal_slice():索引超出范围")
            result_array = image_array[index, :, :]
        elif plane == AnatomicalPlane.SAGITTAL:
            if index < 0 or index >= image_array.shape[2]:
                raise ValueError("NiiLoader::get_coronal_slice():索引超出范围")
            result_array = image_array[:, :, index]
        else:
            raise ValueError("NiiLoader::get_coronal_slice():无效的解剖面")

        return self.__window_level_adjustment(result_array,
            self.__window_width, self.__window_level)

    def get_plane_current_index(self, plane):
        if self.__nii_data is None:
            print('NiiLoader::get_planes_current_index():nii_data is None')
            return None
        if plane == AnatomicalPlane.AXIAL:
            return self.__planes_current_index.get('AXIAL')
        elif plane == AnatomicalPlane.CORONAL:
            return self.__planes_current_index.get('CORONAL')
        elif plane == AnatomicalPlane.SAGITTAL:
            return self.__planes_current_index.get('SAGITTAL')
        else:
            raise ValueError("NiiLoader::get_planes_current_index():无效的解剖面")

    def get_plane_dim(self, plane):
        if self.__nii_data is None:
            print('NiiLoader::get_plane_dim():nii_data is None')
            return None
        image_array = sitk.GetArrayFromImage(self.__nii_data)
        if plane == AnatomicalPlane.AXIAL:
            return image_array.shape[1]
        elif plane == AnatomicalPlane.CORONAL:
            return image_array.shape[0]
        elif plane == AnatomicalPlane.SAGITTAL:
            return image_array.shape[2]
        else:
            raise ValueError("NiiLoader::get_plane_dim():无效的解剖面")

    def set_plane_current_index(self, plane, index):
        if self.__nii_data is None:
            print('NiiLoader::set_planes_current_index():nii_data is None')
            return None
        image_array = sitk.GetArrayFromImage(self.__nii_data)
        if plane == AnatomicalPlane.AXIAL:
            if index < 0 or index >= image_array.shape[1]:
                raise ValueError("NiiLoader::set_coronal_slice():索引超出范围")
            self.__planes_current_index['AXIAL'] = index
        elif plane == AnatomicalPlane.CORONAL:
            if index < 0 or index >= image_array.shape[0]:
                raise ValueError("NiiLoader::set_coronal_slice():索引超出范围")
            self.__planes_current_index['CORONAL'] = index
        elif plane == AnatomicalPlane.SAGITTAL:
            if index < 0 or index >= image_array.shape[2]:
                raise ValueError("NiiLoader::set_coronal_slice():索引超出范围")
            self.__planes_current_index['SAGITTAL'] = index
        else:
            raise ValueError("NiiLoader::set_planes_current_index():无效的解剖面")

    @staticmethod
    def __window_level_adjustment(image_array, window_width, window_level):
        """
        根据窗宽和窗位将图像数据映射到0-255，用于灰度图显示
        :param image_array: 图像数据的 NumPy 数组
        :param window_width: 窗宽
        :param window_level: 窗位
        :return: 调整后的图像数据
        """
        # 计算窗宽和窗位的上下限
        min_window = window_level - (window_width / 2)
        max_window = window_level + (window_width / 2)
        # 映射到0-255
        image_array = (image_array - min_window) / (max_window - min_window+EPS) * 255
        image_array = np.clip(image_array, 0, 255)  # 将值限制在0-255范围内
        image_array = image_array.astype(np.uint8)  # 转换为uint8类型

        # 显示调整后的图像
        # fig, ax = plt.subplots(1, 1, figsize=(10, 5))
        # ax.imshow(image_array, cmap='gray')
        # ax.set_title('Original Image')
        # plt.show()
        return image_array
