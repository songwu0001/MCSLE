import math
from pyproj import Geod
from shapely.geometry import Polygon, Point, MultiPolygon
import geopandas as gpd
from itertools import combinations
GEOD = Geod(ellps="WGS84")

class Pixel2Region:
    def __init__(self, camera_para, shape, maxRange):
        lon_cam = camera_para[0]
        lat_cam = camera_para[1]
        shoot_hdir = camera_para[2]
        shoot_vdir = camera_para[3]
        height_cam = camera_para[4]
        FOV_hor = camera_para[5]
        FOV_ver = camera_para[6]
        width_pic = shape[0]
        height_pic = shape[1]

        self.pixels = dict()
        self.toLonLat = dict()
        self.camera_para = camera_para
        self.shape = shape
        self.maxRange = maxRange


        #the minumum y satisfying being within VANISH_vertical_angle
        minY = -1

        VANISH_vertical_angle = math.degrees(math.atan(self.maxRange / height_cam))
        for x in range(width_pic+1):
            for y in range(height_pic+1):
                Angle_hor = math.degrees(math.atan((x - width_pic//2)/(width_pic//2) * math.tan(math.radians(FOV_hor/2))))
                Angle_ver = math.degrees(math.atan((y - height_pic//2)/(height_pic//2) * math.tan(math.radians(FOV_ver/2))))

                if 90 + shoot_vdir - Angle_ver > VANISH_vertical_angle:
                    continue

                if minY == -1:
                    minY = y

                edgeA = height_cam * math.tan(math.radians(90 + shoot_vdir - Angle_ver))
                edgeC = edgeA / math.cos(math.radians(Angle_hor))
                lon,lat,_ = GEOD.fwd(lon_cam, lat_cam, shoot_hdir + Angle_hor, edgeC)
                self.pixels[str(x) + "," + str(y)] = (lon,lat)

        for x in range(width_pic+1):
            Angle_hor = math.degrees(math.atan((x - width_pic//2)/(width_pic//2) * math.tan(math.radians(FOV_hor/2))))
            edgeA = self.maxRange
            edgeC = edgeA / math.cos(math.radians(Angle_hor))
            lon,lat,_ = GEOD.fwd(lon_cam, lat_cam, shoot_hdir + Angle_hor, edgeC)
            self.pixels[str(x) + "," + str(minY-1)] = (lon,lat)

        for x in range(width_pic):
            for y in range(height_pic):
                if str(x) + "," + str(y) in self.pixels:
                    p1 = self.pixels.get(str(x) + "," + str(y))
                    p2 = self.pixels.get(str(x+1) + "," + str(y))
                    p3 = self.pixels.get(str(x+1) + "," + str(y+1))
                    p4 = self.pixels.get(str(x) + "," + str(y+1))
                    self.toLonLat[str(x) + "," + str(y)] = [(p1,p2),(p2,p3),(p3,p4),(p4,p1)]
        self.minY = minY

    @classmethod
    def getCameras(cls, path):
        with open(path, 'r') as fIn:
            lines = fIn.readlines()[1:]
        answer = []
        for line in lines:
            answer.append(list(map(float, line.strip().split(","))))
        return answer

    def get2LonLat(self):
        return self.toLonLat

    def getMonitorArea(self):
        boundaries = []
        for _ in range(self.shape[1], self.minY-1, -1):
            boundaries.append(self.pixels[str(0)+','+str(_)])
        for _ in range(self.shape[0]):
            boundaries.append(self.pixels[str(_)+','+str(self.minY-1)])
        for _ in range(self.minY-1, self.shape[1]):
            boundaries.append(self.pixels[str(self.shape[0])+','+str(_)])
        for _ in range(self.shape[0], 0, -1):
            boundaries.append(self.pixels[str(_)+','+str(self.shape[1])])
        return Polygon(boundaries)

    def getPolygons(self, pixels):
        '''
        pixels: a set of pixel coords, [(x1, y1), (x2,y2), ...]
        '''
        polygons = []
        for pixel in pixels:
            lines = self.toLonLat[str(pixel[0])+","+str(pixel[1])]
            polygons.append(Polygon([lines[0][0], lines[1][0], lines[2][0], lines[3][0]]))
        return polygons

    def isValid(self, x, y):
        return 0 <= x and x < self.shape[0] and 0 <= y and y < self.shape[1] and (str(x)+","+str(y) in self.pixels)

    def visual_transform_perspective(self, lon_v, lat_v):
        camera_para = self.camera_para
        shape = self.shape

        # 初始化
        lon_cam = camera_para[0]
        lat_cam = camera_para[1]
        shoot_hdir = camera_para[2]
        shoot_vdir = camera_para[3]
        height_cam = camera_para[4]
        FOV_hor = camera_para[5]
        FOV_ver = camera_para[6]
        width_pic = shape[0]
        height_pic = shape[1]

        answer = GEOD.inv(lon_cam, lat_cam, lon_v, lat_v)
        D_abs = answer[-1]
        relative_angle = answer[0]
        Angle_hor = relative_angle - shoot_hdir
        if Angle_hor < -180:
            Angle_hor = Angle_hor + 360
        elif Angle_hor > 180:
            Angle_hor = Angle_hor - 360
        if Angle_hor < -FOV_hor / 2 or Angle_hor > FOV_hor / 2:
            print("beyond horizontal field of view")
            return None

        vertical_angle = math.degrees(math.atan(D_abs * math.cos(math.radians(Angle_hor)) / height_cam))
        VANISH_vertical_angle = math.degrees(math.atan(self.maxRange / height_cam))
        if vertical_angle > VANISH_vertical_angle:
            print("beyond maximum range")
            return None

        Angle_ver = 90 + shoot_vdir - vertical_angle
        if Angle_ver < -FOV_ver / 2 or Angle_ver > FOV_ver / 2:
            print("beyond vertical field of view")
            return None

        target_x1 = int(width_pic//2 * math.tan(math.radians(Angle_hor)) / math.tan(math.radians(FOV_hor/2)))
        target_y1 = int(height_pic//2 * math.tan(math.radians(Angle_ver)) / math.tan(math.radians(FOV_ver/2)))
        target_x1 = (target_x1 + width_pic//2) if Angle_hor >= 0 else (target_x1 + width_pic // 2 - 1)
        target_y1 = (target_y1 + height_pic//2) if Angle_ver >= 0 else (target_y1 + height_pic // 2 - 1)

        for X in [target_x1, target_x1-1, target_x1+1]:
            for Y in [target_y1, target_y1-1, target_y1+1]:
                if self.isValid(X,Y):
                    if gpd.GeoSeries(self.getPolygons([[X,Y],]), crs = 4326).contains(Point(lon_v,lat_v))[0]:
                        return X,Y
        return None

class CameraNet:
    def __init__(self, cameras):
        self.cameras = cameras
        self.cameraParams = [cam.camera_para for cam in cameras]
        self.monitorAreas = [cam.getMonitorArea() for cam in cameras]
        self.imSize = cameras[0].shape

    def guessLonLat(self, pixelsS, withDetails=False):
        '''
        pixelsS are in the format [cam1, cam2, ...]
        each cam#ID is in the format [(x1,y1), (x2,y2), ..] and does not contain duplicates
        '''
        polygonsS = []
        labelsS = []

        for index,e in enumerate(pixelsS):
            polygonsS.append(self.cameras[index].getPolygons(e))
            labelsS.append([(str(index) + "," + str(pixel[0]) + "," + str(pixel[1])) for pixel in e])

        frames = []
        for i in range(len(self.cameras)):
            column = "df" + str(i)
            frame = gpd.GeoDataFrame({"geometry": polygonsS[i], column:labelsS[i]})
            frames.append(frame)

        validIntersections = []
        validPolygons = []
        for num in range(len(self.cameras), 0, -1):
            for comb in combinations(frames, num):
                init = comb[0]
                for k in range(1, num):
                    init = init.overlay(comb[k], how='intersection')
                cols = [col for col in list(init.columns) if col.startswith("df")]
                polygons = list(init["geometry"])
                labels = list(zip(*[list(init[col]) for col in cols]))
                labels = [set(label) for label in labels]
                for k in range(len(polygons)):
                    intersection = labels[k]
                    if not [0 for e in validIntersections if intersection <= e]:
                        if num == len(self.cameras):
                            validPolygons.append(polygons[k])
                            validIntersections.append(intersection)
                        else:
                            whichCameras = [int(e.split(",")[0]) for e in intersection]
                            others = [_ for _ in range(len(self.cameras)) if _ not in whichCameras]
                            polys1 = gpd.GeoSeries([polygons[k]])
                            dfA = gpd.GeoDataFrame({'geometry': polys1, 'dfA':[1]})
                            othersAOI = gpd.GeoSeries([self.monitorAreas[_] for _ in others], crs=4326).unary_union
                            dfB = gpd.GeoDataFrame({'geometry': gpd.GeoSeries(othersAOI), 'dfB':[1]})
                            pure = dfA.overlay(dfB, how='difference')['geometry']
                            if len(pure) > 0:
                                validPolygons.append(pure[0])
                                validIntersections.append(intersection)

        answer = []
        for index in range(len(validPolygons)):
            poly = validPolygons[index]
            poly_ = []
            if poly.geom_type == "Polygon":
                poly_.append(poly)
            else:
                poly_ = poly.geoms

            for polygon in poly_:
                centroid = polygon.centroid
                if withDetails:
                    answer.append([(centroid.x, centroid.y), poly, validIntersections[index]])
                else:
                    answer.append((centroid.x, centroid.y))
        return answer

