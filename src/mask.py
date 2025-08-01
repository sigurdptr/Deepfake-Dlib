from typing import Union, List

import cv2
import numpy as np

from face import FaceModel


class FaceMask:
    def __init__(self, img: cv2.UMat, model: FaceModel) -> None:
        self._face = img
        self._face_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        self._model = model

        convexhull = cv2.convexHull(self._model.points) 
        rect = cv2.boundingRect(convexhull)

        subdiv = cv2.Subdiv2D(rect) # Creates an instance of Subdiv2D
        subdiv.insert(self._model.landmarks) # Insert points into subdiv
        triangles = subdiv.getTriangleList()
        triangles = np.array(triangles, dtype=np.int32)

        indexes_triangles = []

        def get_index(arr):
            index = 0
            if arr[0].any():
                index = arr[0][0]
            return index

        for triangle in triangles:
            # Gets the vertex of the triangle
            pt1 = (triangle[0], triangle[1])
            pt2 = (triangle[2], triangle[3])
            pt3 = (triangle[4], triangle[5])

            index_pt1 = get_index(np.where((self._model.points == pt1).all(axis=1)))
            index_pt2 = get_index(np.where((self._model.points == pt2).all(axis=1)))
            index_pt3 = get_index(np.where((self._model.points == pt3).all(axis=1)))

            # Saves coordinates if the triangle exists and has 3 vertices
            if index_pt1 is not None and index_pt2 is not None and index_pt3 is not None:
                vertices = [index_pt1, index_pt2, index_pt3]
                indexes_triangles.append(vertices)
        
        self._triangles = triangles
        self._indexes_triangles = indexes_triangles
    

    def _fill_triangle(self, ):
        ...


    def apply_mask(self, img: cv2.UMat, models: List[FaceModel]) -> Union[cv2.UMat, None]:
        if len(models) == 0:
            return

        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        output = img.copy()

        for model in models:
            height, width, channels = img.shape
            new_face = np.zeros((height, width, channels), np.uint8)
            
            conexhull = cv2.convexHull(model.points)

            for triangle in self._indexes_triangles:
                # Coordinates of the first person's delaunay triangles
                pt1 = self._model.landmarks[triangle[0]]
                pt2 = self._model.landmarks[triangle[1]]
                pt3 = self._model.landmarks[triangle[2]]

                # Gets the delaunay triangles
                (x, y, widht, height) = cv2.boundingRect(np.array([pt1, pt2, pt3], np.int32))
                cropped_triangle = self._face[y: y+height, x: x+widht]
                cropped_mask = np.zeros((height, widht), np.uint8)

                # Fills triangle to generate the mask
                points1 = np.array([[pt1[0]-x, pt1[1]-y], [pt2[0]-x, pt2[1]-y], [pt3[0]-x, pt3[1]-y]], np.int32)
                cv2.fillConvexPoly(cropped_mask, points1, 255)

                # Coordinates of the person's delaunay triangles
                pt1 = model.landmarks[triangle[0]]
                pt2 = model.landmarks[triangle[1]]
                pt3 = model.landmarks[triangle[2]]

                # Gets the delaunay triangles
                (x, y, widht, height) = cv2.boundingRect(np.array([pt1, pt2, pt3], np.int32))
                cropped_mask2 = np.zeros((height,widht), np.uint8)

                # Fills triangle to generate the mask
                points2 = np.array([[pt1[0]-x, pt1[1]-y], [pt2[0]-x, pt2[1]-y], [pt3[0]-x, pt3[1]-y]], np.int32)
                cv2.fillConvexPoly(cropped_mask2, points2, 255)

                # Deforms the triangles to fit the subject's self._face : https://docs.opencv.org/3.4/d4/d61/tutorial_warp_affine.html
                points1 = np.float32(points1)
                points2 = np.float32(points2)
                M = cv2.getAffineTransform(points1, points2)  # Warps the content of the first triangle to fit in the second one
                dist_triangle = cv2.warpAffine(cropped_triangle, M, (widht, height))
                dist_triangle = cv2.bitwise_and(dist_triangle, dist_triangle, mask=cropped_mask2)

                # Joins all the distorted triangles to make the self._face mask to fit in the second person's features
                body_new_face_rect_area = new_face[y: y+height, x: x+widht]
                body_new_face_rect_area_gray = cv2.cvtColor(body_new_face_rect_area, cv2.COLOR_BGR2GRAY)

                # Creates a mask
                masked_triangle = cv2.threshold(body_new_face_rect_area_gray, 1, 255, cv2.THRESH_BINARY_INV)
                dist_triangle = cv2.bitwise_and(dist_triangle, dist_triangle, mask=masked_triangle[1])

                # Adds the piece to the self._face mask
                body_new_face_rect_area = cv2.add(body_new_face_rect_area, dist_triangle)
                new_face[y: y+height, x: x+widht] = body_new_face_rect_area
            
            face_mask = np.zeros_like(img_gray)
            head_mask = cv2.fillConvexPoly(face_mask, conexhull, 255)
            face_mask = cv2.bitwise_not(head_mask)

            body_maskless = cv2.bitwise_and(img, img, mask=face_mask)
            result = cv2.add(body_maskless, new_face)

            x, y, widht, height = cv2.boundingRect(conexhull)
            center_face2 = (int((x+x+widht)/2), int((y+y+height)/2))

            output = cv2.seamlessClone(result, output, head_mask, center_face2, cv2.NORMAL_CLONE)
        
        return output