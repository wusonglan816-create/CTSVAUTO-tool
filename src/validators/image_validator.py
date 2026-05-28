from __future__ import annotations


class ImageValidator:
    def similarity_at_least(self, actual_path: str, reference_path: str, threshold: float) -> bool:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("opencv-python is required for image validation") from exc

        actual = cv2.imread(actual_path, cv2.IMREAD_GRAYSCALE)
        reference = cv2.imread(reference_path, cv2.IMREAD_GRAYSCALE)
        if actual is None or reference is None:
            return False
        score = cv2.matchTemplate(actual, reference, cv2.TM_CCOEFF_NORMED)[0][0]
        return bool(score >= threshold)
