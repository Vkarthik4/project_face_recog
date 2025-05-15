This Project is an AI-powered virtual classroom monitoring system that automates student attendance and ensures active participation using real-time facial recognition and behavior analysis. It features a PyQt5-based faculty interface that displays a fullscreen webcam feed alongside a mini student camera stream via UDP, integrates YOLOv8 for face detection, MobileFaceNet and Dlib for facial embedding and alignment, and uses phone detection to flag distractions. A countdown timer tracks session time, while participation is continuously assessed based on facial presence, alignment, and attention, ensuring secure, interactive, and intelligent class monitoring.

In terms of performance, YOLOv8 achieves around 95% accuracy in face detection under good lighting, making it the most efficient for real-time scenarios. MobileFaceNet, due to its lightweight architecture, delivers fast inference with over 90% recognition accuracy, suitable for embedded systems. Dlib’s face alignment improves embedding quality but adds slight computational overhead. A drawback is that YOLOv8's accuracy drops in poor lighting, and MobileFaceNet can misclassify at extreme angles. Phone detection via OpenCV has limitations under occlusion or non-standard devices. Overall, the combination balances speed and accuracy effectively for classroom automation.

Steps to run code->
1) git clone https://github.com/Vkarthik4/project_face_recog.git
2) in cmd: pip -m venv <filename>(your choice)
3) in cmd: pip install <packagename>(whatever its telling to install)

Infos:
1) In code there is need to use 2 camera one default n other your choice, if u planning to use mobile as second camera then follow below:
  a) install from google -> obs studio (for to preview camera) , camo stuido(if for to manage the camera)
2) dont use more than 3 camera, cause it uses latest index to camera(i mean uses 2 position to see any camera present in that location, change code index value of cam if u want)
3) do face reco. in bright light to detect and have good cam quality to detect active particpation by ai
4) it can predict the phone if u se for proxy
5) voice system isnt added and also pyaudio is used but it wont work cause havent fixed it, working on it
