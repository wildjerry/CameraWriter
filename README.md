# Camera Writer

## The Challenge
TODO: add official challenge description

Provide a way to write text using the webcam.

## The plan
I see two ways to do this.

1. Take the position of some body part on the screen(nose, hand, etc). Directly use the positon on camera to draw.
2. Use the position of 2 parts in 3d space to get a line where the user is looking/pointing. Then, project onto a plane in order to write.

My goal is to implement option 2 because it's both a more interesting challenge, and should be easier to use(turning your head or point tends to be more intuitive than translating position)

Steps:

1. Get pose using mediapipe
2. Get x, y, z coordinates of pre-chosen landmarks using `landmark.x`, `landmark.y`, `landmark.z`
3. Find the vector between them by subtracting
4. Get intersection with plane(aligned to webcam for convenince) by finding scalar transform to make the vectors tail fall on the z,
then multiplying the x and y components by the same amount
5. Plot line from last x and y to current x and y using cv2.line()

Stretch goals:
1. Color control
2. Support multiple parts for tracking (face may need to calculate a normal to a plane defined by 3 points)
3. multiperson support(works by iterating over list rather than selecting just one)
4. Allow projecting to a plane not aligned with the webcam, for instance to allow the use of external webcams. One way to do this would be to use the vector to create a parameterization of a line, than find the intersections with the plane.