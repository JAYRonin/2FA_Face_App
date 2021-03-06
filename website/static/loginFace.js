const API_URL = "http://127.0.0.1:5000"

// Załadowanie modeli po stronie klienta
Promise.all([
  faceapi.nets.tinyFaceDetector.loadFromUri('/static/models'),
  faceapi.nets.faceLandmark68Net.loadFromUri('/static/models'),
  faceapi.nets.faceRecognitionNet.loadFromUri('/static/models'),
]).then(startVideo)

// Uruchomienie systemu biometrycznego; upewni się że kamera jest włączona oraz że modele zostały załadowane
function startVideo() {
  const video = document.getElementById('video')
  console.log(video)
  
  video && video.addEventListener('play', () => {
    const canvas = faceapi.createCanvasFromMedia(video)
    const videoContainer = document.getElementById('videoContainer')
    videoContainer && videoContainer.append(canvas)
    const displaySize = { width: video.width, height: video.height }
    faceapi.matchDimensions(canvas, displaySize)
    
    setInterval(async () => {
      this.detections = await faceapi.detectAllFaces(video, new faceapi.TinyFaceDetectorOptions()).withFaceLandmarks().withFaceDescriptors()
      const resizedDetections = faceapi.resizeResults(detections, displaySize)
      canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height)
      faceapi.draw.drawDetections(canvas, resizedDetections)
    }, 100)
  })

  video && navigator.getUserMedia(
    { video: {} },
    stream => video.srcObject = stream,
    err => console.error(err)
  )
  setInterval(() => this.sendDescriptor(), 5000) // uruchamianie sendDescriptor co 2 sekundy
}

// Komunikacja klient <-> serwer
async function sendDescriptor() {
  if (this.detections[0] === undefined) {
    console.log('error catched')
    axios.post(`${API_URL}/login-face`, {
      encodings: 'undefined'
    })
    .then((res) => {
      console.log(res);
      if(res.status === 204) {
        window.location.href = `${API_URL}/login-face`;
    }
    })
    .catch(function (error) {
      console.log(error);
    });
  }
  else {
    axios.post(`${API_URL}/login-face`, {
      encodings: this.detections[0].descriptor
    })
    .then((res) => {
      console.log(res);
      if(res.status === 200) {
        window.location.href = `${API_URL}`;
      }
      // response dla próby włamania
      if(res.status === 401) {
        window.location.href = `${API_URL}/login`;
      }
    })
    .catch(function (error) {
      console.log(error);
    });
  }
}