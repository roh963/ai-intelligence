import dlib 
import numpy as np 
import face_recognition_models
from sklearn.svm import SVC
from functools import lru_cache
from app.services.helper_service import get_all_students
import cv2

@lru_cache(maxsize=1)
def load_dlib_models():
    
    # STEP 1: The Face Finder
    # This uses a HOG (Histogram of Oriented Gradients) algorithm to scan the image.
    # It looks for general face patterns (like the 'V' shape of a chin or the shadow of eyes) 
    # and draws a bounding box around any face it finds.
    detector = dlib.get_frontal_face_detector()


    # STEP 2: The Landmark Locator
    # Once we have a face box, we need to know exactly where the features are.
    # This model identifies specific 'landmarks' (like the corners of the eyes and the tip of the nose) 
    # to make sure the face is centered and rotated correctly before we analyze it.
    sp = dlib.shape_predictor(
        face_recognition_models.pose_predictor_five_point_model_location()
    )


    # STEP 3: The Identity Encoder (The "Face Fingerprint")
    # This is a Deep Neural Network that turns a face into a list of 128 unique numbers.
    # Think of this as a digital "fingerprint." If two different photos produce 
    # nearly the same 128 numbers, the computer knows it's the same person.
    facereconize = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )

    return detector , sp , facereconize


# def get_face_embeddings(image_np):
#     # ── Dlib-safe image prep ──────────────────────────────────────────────────
#     # np.ascontiguousarray returns a VIEW when array is already contiguous,
#     # and dlib rejects views (OWNDATA=False).  .copy() always creates a fresh
#     # owned, writeable, C-contiguous array — the only format dlib accepts.
#     img = np.array(image_np, dtype=np.uint8)   # ensure uint8
#     if img.ndim == 3 and img.shape[2] == 4:    # RGBA → RGB
#         img = img[:, :, :3]
#     img = np.ascontiguousarray(img, dtype=np.uint8).copy()  # owned copy
#     # ─────────────────────────────────────────────────────────────────────────
#     detector, sp, facereconize = load_dlib_models()
#     faces = detector(img, 1)
#     encodings = []

#     for face in faces:
#         shape = sp(img, face)
#         face_descriptor = facereconize.compute_face_descriptor(img, shape, 1)  # 128 embedding
#         encodings.append(np.array(face_descriptor))
#     return encodings


# def get_face_embeddings(image_np):
#     # image already RGB uint8 owned array hai (_decode_image ne ensure kiya)
#     # Bas ek fresh C-contiguous owned copy banao — koi conversion nahi
#     img = np.ascontiguousarray(image_np, dtype=np.uint8).copy()
#     img.flags.writeable = True

#     # TEMPORARILY ADD - dekho kya aa raha hai
#     print(f"dtype: {img.dtype}")
#     print(f"shape: {img.shape}")
#     print(f"ndim: {img.ndim}")
#     print(f"C_CONTIGUOUS: {img.flags['C_CONTIGUOUS']}")
#     print(f"OWNDATA: {img.flags['OWNDATA']}")
#     print(f"WRITEABLE: {img.flags['WRITEABLE']}")

#     detector, sp, facereconize = load_dlib_models()
#     faces = detector(img, 1)

#     encodings = []
#     for face in faces:
#         shape = sp(img, face)
#         face_descriptor = facereconize.compute_face_descriptor(img, shape, 1)
#         encodings.append(np.array(face_descriptor))
#     return encodings

def get_face_embeddings(image_np):
    # np.require — dlib ke liye guaranteed safe array
    img = np.require(image_np, dtype=np.uint8, requirements=['C', 'O', 'W'])

    print("image the np array",img)
    
    detector, sp, facereconize = load_dlib_models()

    print("detector:",detector)
    print("sp:",sp)
    print("facereconize:",facereconize)

    
    faces = detector(img, 1)

    encodings = []
    for face in faces:
        shape = sp(img, face)
        face_descriptor = facereconize.compute_face_descriptor(img, shape, 1)
        encodings.append(np.array(face_descriptor))
    return encodings

@lru_cache(maxsize=1)
def get_trained_model():
    X = [] # embedding 
    y = [] # id 
    student_db = get_all_students()

    if not student_db:
        return None 
    
    for student in student_db:
        embedding = student.get('face_embedding')
        if embedding:
            X.append(np.array(embedding))
            y.append(student.get('student_id'))
        
    if len(X) == 0:
            return 0
        
    clf = SVC(kernel='linear',probability=True, class_weight='balanced')

    try:
        clf.fit(X,y)
    except ValueError:
         pass

    return {'clf':clf , 'X':X , 'y':y}


def train_classifier():
    get_trained_model.cache_clear()   # st.cache_resource.clear() ka exact alternative
    model_data = get_trained_model()

    return bool(model_data)

def predict_attendace(class_image_np):
    encodings = get_face_embeddings(class_image_np)

    detected_student ={}

    model_data = get_trained_model()

    if not model_data:
        return {} , [] , len(encodings)
    
    clf = model_data['clf']
    X_train= model_data['X']
    y_train= model_data['y']

    all_student = sorted(list(set(y_train)))

    for encoding in encodings:
        if len(all_student)>=2:
            predicted_id = int(clf.predict([encoding])[0])
        else:
            predicted_id= int(all_student[0])

        student_embedding = X_train[y_train.index(predicted_id)]

        best_match_score = np.linalg.norm(student_embedding - encoding)

        resemblance_threshold =0.6

        if best_match_score <= resemblance_threshold:
            detected_student[predicted_id] = True
    
    return detected_student, all_student, len(encodings)


