import streamlit as st
import cv2
from PIL import Image
import os
import numpy as np
import tensorflow as tf
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as viz_utils
from object_detection.builders import model_builder
from object_detection.utils import config_util

# Set the path to the protoc binary
os.environ['PATH'] += ':/Tensorflow/protoc'


CUSTOM_MODEL_NAME = 'my_ssd_mobnet'
paths = {
    'CHECKPOINT_PATH': os.path.join('Tensorflow', 'workspace', 'models', CUSTOM_MODEL_NAME),
    'LABELMAP': os.path.join('Tensorflow', 'workspace', 'annotations', 'label_map.pbtxt')
}

configs = config_util.get_configs_from_pipeline_file(os.path.join(paths['CHECKPOINT_PATH'], 'pipeline.config'))
detection_model = model_builder.build(model_config=configs['model'], is_training=False)
ckpt = tf.compat.v2.train.Checkpoint(model=detection_model)
ckpt.restore(os.path.join(paths['CHECKPOINT_PATH'], 'ckpt-3')).expect_partial()
category_index = label_map_util.create_category_index_from_labelmap(paths['LABELMAP'])


@tf.function
def detect_fn(image):
    image, shapes = detection_model.preprocess(image)
    prediction_dict = detection_model.predict(image, shapes)
    detections = detection_model.postprocess(prediction_dict, shapes)
    return detections


def main():
    st.title('Furniture Detection')

    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png", "jpeg"])

    if uploaded_file is not None:
        image = np.array(Image.open(uploaded_file))
        st.image(image, caption='Uploaded Image', use_column_width=True)
        st.write("")
        st.write("Detection In Process...")

        
        input_tensor = tf.convert_to_tensor(np.expand_dims(image, 0), dtype=tf.float32)
        detections = detect_fn(input_tensor)

        num_detections = int(detections.pop('num_detections'))
        detections = {key: value[0, :num_detections].numpy() for key, value in detections.items()}
        detections['num_detections'] = num_detections
        detections['detection_classes'] = detections['detection_classes'].astype(np.int64)

        label_id_offset = 1
        image_np_with_detections = image.copy()

        viz_utils.visualize_boxes_and_labels_on_image_array(
            image_np_with_detections,
            detections['detection_boxes'],
            detections['detection_classes'] + label_id_offset,
            detections['detection_scores'],
            category_index,
            use_normalized_coordinates=True,
            max_boxes_to_draw=5,
            min_score_thresh=.3,
            agnostic_mode=False
        )

        st.image(image_np_with_detections, caption='Detected Teeth', use_column_width=True)

if __name__ == "__main__":
    main()
