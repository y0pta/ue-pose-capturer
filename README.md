### UE pose capturer
---
The script generateData.py allows render RGBD data from UE4 game binary. Sample model could be obtained in <*renderModel*> directory.
To generete RGBD data you should provide trajectory of camera movement, width. height and fov of target camera.
### Usage
---
```sh
> generateData.py [-h] [-W <int>] [-H <int>] [--fov <int>] [-k] <workdir model_name
```
##### Positional arguments:
| ARG | DESCRIPTION |
| ------ | ------ |
| workdir | working directory with .exe |
| model_name | name of model for | 

As a result game binary path: <workdir>/renderModel/<model_name>.exe.
**workdir** should contain:
- renderModel - folder with UE4 game built with UE4 plugin;
- trajectoryUE.txt - file, where each line is 6 coords in UE4 [x y z pitch yaw roll] [cm, degrees]

##### Optional arguments:
| ARG | DESCRIPTION |
| ------ | ------ |
| -h, --help|  show this help message and exitTo generatr |
|-W <int> |       width of rendering, by default 1280 |
| -H <int> |       height of rendering, by default 960 |
| --fov <int> |  field of view for renders in degrees, by default 80|
| -k <int>   |     K_depth for depth-maps, by default 5000 |
##### Run example
```sh
> python.exe /d/UE/ modernHome -W=640 -H=480 -k=5000 --fov=60
```
This command will generate following content,placed in <workdir>:
- folders images_WxH/, depths_WxH/ with .png pictures;
- file trajectory.txt - trajectory in ibr-format [rot_x rot_y rot_z x y z] [radians, m];
- file intrinsics_FOV<fov>_<W>x<H>.txt - camera intrinsics matrix.
##### Models 
You can check avaliable models here.
http://docs.unrealcv.org/en/master/reference/model_zoo.html#realisticrendering
