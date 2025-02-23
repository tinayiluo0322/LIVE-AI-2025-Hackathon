import * as cocoSsd from '@tensorflow-models/coco-ssd';
import '@tensorflow/tfjs';

const loadScript = (src) => {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) {
      resolve();
      return;
    }
    
    const script = document.createElement('script');
    script.src = src;
    script.async = true;
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });
};

export const loadMediaPipe = async () => {
  try {
    if (window.Hands) return true;

    await Promise.all([
      loadScript('https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1646424915/hands.js'),
      loadScript('https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils@0.3.1/drawing_utils.js'),
      loadScript('https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils@0.3.1/camera_utils.js')
    ]);

    // Add a small delay to ensure scripts are properly initialized
    await new Promise(resolve => setTimeout(resolve, 200));
    return true;
  } catch (error) {
    console.error('MediaPipe loading error:', error);
    throw error;
  }
};

export const loadTensorFlow = async () => {
  try {
    await cocoSsd.load();
    return true;
  } catch (error) {
    console.error('TensorFlow loading error:', error);
    throw error;
  }
};

const initializeHands = async () => {
  const hands = new window.Hands({
    locateFile: (file) => 
      `https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1646424915/${file}`
  });

  await hands.initialize();

  hands.setOptions({
    maxNumHands: 1,
    modelComplexity: 1,
    minDetectionConfidence: 0.5,
    minTrackingConfidence: 0.5
  });

  return hands;
};

const simulateKeyPress = (splineRef) => {
  const keyDownEvent = new KeyboardEvent('keydown', {
    key: 'w',
    code: 'KeyW',
    keyCode: 87,
    which: 87,
    bubbles: true,
    cancelable: true
  });
  document.dispatchEvent(keyDownEvent);

  if (splineRef.current) {
    splineRef.current.emitEvent('keyDown', { key: 'w' });
  }

  setTimeout(() => {
    const keyUpEvent = new KeyboardEvent('keyup', {
      key: 'w',
      code: 'KeyW',
      keyCode: 87,
      which: 87,
      bubbles: true,
      cancelable: true
    });
    document.dispatchEvent(keyUpEvent);

    if (splineRef.current) {
      splineRef.current.emitEvent('keyUp', { key: 'w' });
    }
  }, 100);
};

export const initTracking = async (
  videoRef,
  canvasRef,
  mediaStreamRef,
  personDetectionRef,
  handsRef,
  characterRef,
  splineRef,
  setMessage,
  setCameraActive
) => {
  let detectionLoop = null;

  try {
    // Initialize person detection
    personDetectionRef.current = await cocoSsd.load();
    
    // Initialize hands with retry mechanism
    let retryCount = 0;
    while (retryCount < 3) {
      try {
        handsRef.current = await initializeHands();
        break;
      } catch (error) {
        retryCount++;
        console.error(`Hand initialization attempt ${retryCount} failed:`, error);
        if (retryCount === 3) throw error;
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }

    // Setup hand tracking results handler
    handsRef.current.onResults((results) => {
      if (!canvasRef.current || !videoRef.current) return;
      
      const ctx = canvasRef.current.getContext('2d');
      if (!ctx) return;

      // Clear and draw video frame
      ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
      ctx.drawImage(
        videoRef.current, 
        0, 
        0, 
        canvasRef.current.width, 
        canvasRef.current.height
      );

      // Process hand landmarks if detected
      if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
        const landmarks = results.multiHandLandmarks[0];

        // Draw hand connections and landmarks
        if (window.drawConnectors && window.drawLandmarks) {
          window.drawConnectors(
            ctx,
            landmarks,
            window.HAND_CONNECTIONS,
            { color: '#00FF00', lineWidth: 3 }
          );
          window.drawLandmarks(
            ctx,
            landmarks,
            { color: '#FF0000', lineWidth: 2 }
          );
        }

        // Detect wave gesture
        const wrist = landmarks[0];
        const tipOfMiddleFinger = landmarks[12];
        
        if (tipOfMiddleFinger.y < wrist.y - 0.1) { // Added threshold for more reliable detection
          console.log('Wave gesture detected!');
          simulateKeyPress(splineRef);
          setTimeout(() => setMessage(''), 2000);
        }
      }
    });

    // Setup continuous detection loop
    const detect = async () => {
      if (!videoRef.current || !mediaStreamRef.current) return;
      
      try {
        // Person detection
        const predictions = await personDetectionRef.current.detect(videoRef.current);
        const personPredictions = predictions.filter(pred => pred.class === 'person');
        
        if (personPredictions.length > 0) {
          const mainPerson = personPredictions.reduce((largest, current) => 
            current.bbox[2] * current.bbox[3] > largest.bbox[2] * largest.bbox[3] 
              ? current 
              : largest
          );

          // Update character rotation based on person position
          if (characterRef.current) {
            const frameWidth = videoRef.current.videoWidth;
            const frameHeight = videoRef.current.videoHeight;
            const personCenterX = mainPerson.bbox[0] + mainPerson.bbox[2] / 2;
            const personCenterY = mainPerson.bbox[1] + mainPerson.bbox[3] / 2;

            const normalizedX = ((personCenterX / frameWidth) - 0.5) * 2;
            const normalizedY = ((personCenterY / frameHeight) - 0.5) * 2;

            // Apply smooth rotation
            const smoothingFactor = 0.3;
            const maxRotationAngle = Math.PI / 2;

            characterRef.current.rotation.y = characterRef.current.rotation.y * (1 - smoothingFactor) + 
                                          (-normalizedX * maxRotationAngle) * smoothingFactor;
            characterRef.current.rotation.x = characterRef.current.rotation.x * (1 - smoothingFactor) + 
                                          (normalizedY * maxRotationAngle) * smoothingFactor;

            // Dampen rotation
            characterRef.current.rotation.y *= 0.9;
            characterRef.current.rotation.x *= 0.9;
          }
        }

        // Process hand tracking
        if (videoRef.current) {
          await handsRef.current.send({ image: videoRef.current });
        }

      } catch (error) {
        console.error('Detection error:', error);
      }
      
      // Continue detection loop
      detectionLoop = requestAnimationFrame(detect);
    };

    // Start detection loop
    detect();

    // Return cleanup function
    return () => {
      if (detectionLoop) {
        cancelAnimationFrame(detectionLoop);
      }
      if (handsRef.current) {
        handsRef.current.close();
      }
    };

  } catch (error) {
    console.error('Error in tracking setup:', error);
    setCameraActive(false);
    throw error;
  }
};