import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Application } from '@splinetool/runtime';
import OpenAI from 'openai';
import { 
  loadTensorFlow, 
  loadMediaPipe, 
  initTracking 
} from './tracking-utils';
import {Logo} from './NeoAssistantStyles';
import logo from './logo.png';
import { 
  Container, 
  SplineContainer, 
  SpeechBubbleContainer, 
  SpeechBubble, 
  HiddenVideo, 
  HandTrackingCanvas,
  LeftHalf,
  RightHalf,
  EntityCard,
  EntityImage,
  EntityExplanation,
  EntityImagePlaceholder,
  LoadingSpinner
} from './NeoAssistantStyles';

const NeoInteractiveAssistant = () => {
  // Refs
  const splineRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const handCanvasRef = useRef(null);
  const characterRef = useRef(null);
  const recognitionRef = useRef(null);
  const openaiRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const personDetectionRef = useRef(null);
  const handsRef = useRef(null);

  // State
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [message, setMessage] = useState('');
  const [isMessageVisible, setIsMessageVisible] = useState(true);
  const [cameraActive, setCameraActive] = useState(true);
  const [trackingInitialized, setTrackingInitialized] = useState(false);
  const [extractedEntities, setExtractedEntities] = useState([]);
  const [voices, setVoices] = useState([]);
  const [overviewText, setOverviewText] = useState('');
  const [currentSpeechQueue, setCurrentSpeechQueue] = useState([]);
  
  // Initialize OpenAI
  useEffect(() => {
    if (process.env.REACT_APP_OPENAI_API_KEY) {
      openaiRef.current = new OpenAI({
        apiKey: process.env.REACT_APP_OPENAI_API_KEY,
        dangerouslyAllowBrowser: true
      });
    }
  }, []);

  // Load Spline Scene
  useEffect(() => {
    const loadSpline = async () => {
      if (!canvasRef.current) return;
      
      try {
        const app = new Application(canvasRef.current);
        await app.load('https://prod.spline.design/YY8JN5JSwskEgOqC/scene.splinecode');
        
        splineRef.current = app;
        const character = app.findObjectByName('Chicken');
        if (character) {
          characterRef.current = character;
        }
      } catch (error) {
        console.error('Failed to load Spline:', error);
      }
    };
    
    loadSpline();
  }, []);

  // Initialize camera and tracking
  useEffect(() => {
    let cleanup = false;
    

    const greetUser = () => {
      const greetingMessage = "Hello! I'm Neo, your AI learning buddy. Let's explore something amazing together!";
      speakResponse(greetingMessage, true); // Note the true flag to keep it in overview
    };

    const initializeSystem = async () => {
      if (!cameraActive || cleanup) return;

      try {
        // First load scripts
        await loadMediaPipe();
        await loadTensorFlow();
        
        // Wait for scripts to initialize
        await new Promise(resolve => setTimeout(resolve, 500));
        
        if (cleanup) return;

        // Get camera stream
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480, facingMode: 'user' }
        });
        
        if (cleanup) {
          stream.getTracks().forEach(track => track.stop());
          return;
        }

        mediaStreamRef.current = stream;
        
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await new Promise((resolve) => {
            videoRef.current.onloadedmetadata = resolve;
          });
          await videoRef.current.play();
        }

        // Initialize tracking
        await initTracking(
          videoRef,
          handCanvasRef,
          mediaStreamRef,
          personDetectionRef,
          handsRef,
          characterRef,
          splineRef,
          setMessage,
          setCameraActive
        );

        setTrackingInitialized(true);
        greetUser();
        
      } catch (error) {
        console.error('System initialization error:', error);
        if (!cleanup) {
          setCameraActive(false);
          setTrackingInitialized(false);
        }
      }
    };

    initializeSystem();

    return () => {
      cleanup = true;
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, [cameraActive]);

  useEffect(() => {
    if (!('webkitSpeechRecognition' in window)) {
      console.error('Speech Recognition not supported');
      return;
    }
  
    const recognition = new window.webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    
    recognition.onstart = () => {
      console.log('Started listening');
      setIsListening(true);
      setMessage("I'm listening...");
    };
  
    recognition.onresult = (event) => {
      if (event.results && event.results[0]) {
        const transcript = event.results[0][0].transcript.trim();
        console.log('Recognized speech:', transcript);
        setIsListening(false);
        handleUserInput(transcript);
      }
    };
  
    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event);
      setIsListening(false);
      setMessage("Sorry, I couldn't hear you clearly. Can you try again?");
    };
  
    recognition.onend = () => {
      console.log('Speech recognition ended');
      setIsListening(false);
    };
  
    recognitionRef.current = recognition;
  }, []);

  // Add this effect right after your speech recognition effect:
useEffect(() => {
  const initVoices = () => {
    const availableVoices = window.speechSynthesis.getVoices();
    setVoices(availableVoices);
  };

  if (window.speechSynthesis.onvoiceschanged !== undefined) {
    window.speechSynthesis.onvoiceschanged = initVoices;
  }
  initVoices();
}, []);

const generateConceptsAndImages = async (input) => {
  try {
    const conceptResponse = await openaiRef.current.chat.completions.create({
      model: "gpt-3.5-turbo",
      messages: [
        {
          role: "system",
          content: `Create 3 educational concepts about the topic for a 10-year-old.
          Focus on clear, engaging explanations that are easy to understand.
          Format as JSON: {
            "concepts": [
              {
                "explanation": "A clear, comprehensive explanation that breaks down the concept into 2-3 sentences using simple, engaging language.",
                "imageDescription": "A detailed description for creating an educational illustration"
              }
            ]
          }`
        },
        { role: "user", content: input }
      ],
      response_format: { type: "json_object" }
    });

    const conceptData = JSON.parse(conceptResponse.choices[0].message.content);
    
    // Generate images for concepts
    const conceptsWithImages = await Promise.all(
      conceptData.concepts.map(async (concept) => {
        try {
          const imageResponse = await openaiRef.current.images.generate({
            model: "dall-e-3",
            prompt: `Create an educational illustration that clearly explains ${concept.imageDescription}. 
            Make it simple, clear, and engaging for a 10-year-old. Avoid texts in the image.
            Use bright colors and clear, easy-to-understand details.`,
            n: 1,
            size: "1024x1024",
            quality: "hd",
            style: "vivid"
          });

          return {
            explanation: concept.explanation,
            imageUrl: imageResponse.data[0].url
          };
        } catch (error) {
          console.error('Image generation failed:', error);
          return concept;
        }
      })
    );

    return conceptsWithImages;
  } catch (error) {
    console.error('Concept generation error:', error);
    throw error;
  }
};
  
  const extractConcepts = async (input) => {
    const response = await openaiRef.current.chat.completions.create({
      model: "gpt-3.5-turbo",
      messages: [
        {
          role: "system",
          content: `Extract exactly 3 key concepts from this topic that would fascinate a 10-year-old.
          Format as JSON with structure:
          {
            "concepts": [
              {
                "name": "Unique Concept Name",
                "explanation": "Simple, factually accurate but fascinating explanation of the concept for a 10 years old child",
                "imagePrompt": "Detailed prompt for generating a hyperrealistic image of this concept"
              }
            ]
          }`
        },
        { role: "user", content: input }
      ],
      response_format: { type: "json_object" }
    });
  
    const parsedResponse = JSON.parse(response.choices[0].message.content);
    console.log('Extracted concepts:', parsedResponse);
    return parsedResponse.concepts;
  };
  
  const generateImage = async (concept) => {
    const imagePrompt = `Create a hyperrealistic, highly detailed image of ${concept.name}. 
      The image should be educational and fascinating for a 10-year-old.
      Focus on ${concept.imagePrompt}.
      Style: Hyperrealistic, 8K quality, dramatic lighting, detailed textures.`;
  
    const imageResponse = await openaiRef.current.images.generate({
      model: "dall-e-3",
      prompt: imagePrompt,
      n: 1,
      size: "1024x1024",
      quality: "hd",
      style: "vivid"
    });
  
    return imageResponse.data[0].url;
  };
   

 // Add a queue for speech responses
const speechQueue = [];
let isSpeakingInProgress = false;


// Ensure voices are loaded
useEffect(() => {
  const loadVoices = () => {
    const voices = window.speechSynthesis.getVoices();
    const googleUKFemale = voices.find(voice => voice.name === 'Google UK English Female');
    
    if (!googleUKFemale) {
      console.warn('Google UK English Female voice not found');
    }
  };

  // Modern browsers
  if (window.speechSynthesis.onvoiceschanged !== undefined) {
    window.speechSynthesis.onvoiceschanged = loadVoices;
  }

  // Immediate call
  loadVoices();
}, []);

// Modify voices initialization effect
useEffect(() => {
  const initVoices = () => {
    const availableVoices = window.speechSynthesis.getVoices();
    console.log('Total voices:', availableVoices.length);
    availableVoices.forEach((voice, index) => {
      console.log(`Voice ${index}:`, voice.name, voice.lang);
    });
    setVoices(availableVoices);
  };

  // Modern browsers
  if ('onvoiceschanged' in window.speechSynthesis) {
    window.speechSynthesis.onvoiceschanged = initVoices;
  }

  // Immediate call
  initVoices();
}, []);

const handleUserInput = async (input) => {
  if (!openaiRef.current) return;

  try {
    setIsProcessing(true);
    
    // Clear any existing speech queue
    setCurrentSpeechQueue([]);
    
    // Immediate thinking response
    await speakResponse("Thinking...");

    // Start both overview and concept generation simultaneously
    const [overview, concepts] = await Promise.all([
      generateOverview(input),
      generateConceptsAndImages(input)
    ]);

    // Speak the overview
    await speakResponse(overview, true);

    // Set entities immediately to start image loading
    setExtractedEntities(concepts);

    // Prepare introductions for concepts
    const introductions = [
      `Let's explore this fascinating idea:`,
      `Here's an incredible insight:`,
      `Check out this amazing discovery:`,
      `Prepare to be amazed:`,
      `Here's something really interesting:`
    ];

    // Speak about each concept sequentially
    for (const concept of concepts) {
      const intro = introductions[Math.floor(Math.random() * introductions.length)];
      const fullExplanation = `${intro} ${concept.explanation}`;
      
      await speakResponse(fullExplanation);
    }

    await speakResponse("What would you like to learn about next?");

  } catch (error) {
    console.error('Error processing input:', error);
    await speakResponse("Oops! I'm having trouble understanding. Could you try again?");
  } finally {
    setIsProcessing(false);
  }
};

const generateOverview = async (input) => {
  try {
    const response = await openaiRef.current.chat.completions.create({
      model: "gpt-3.5-turbo",
      messages: [
        {
          role: "system",
          content: "You are explaining to a 10-year-old. Provide a simple, 2-3 sentences, factually accurate overview that captures the essence of the topic in a way that's easy to understand and exciting to listen to."
        },
        { role: "user", content: input }
      ],
      temperature: 0.7,
      max_tokens: 250, // Increased token limit
      top_p: 0.9, // More diverse response
      frequency_penalty: 0.5, // Reduce repetition
      presence_penalty: 0.5 // Encourage novel content
    });

    // Get the full content of the response
    const overviewText = response.choices[0].message.content.trim();
    
    console.log('Generated Overview:', overviewText); // Debugging log

    return overviewText;
  } catch (error) {
    console.error('Overview generation error:', error);
    return "I found something interesting about this topic that I'd love to share with you!";
  }
};

const speakResponse = (text, isOverview = false) => {
  return new Promise((resolve, reject) => {
    if (!text) {
      resolve();
      return;
    }

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    
    // Get all voices and find a suitable English female voice
    const voices = window.speechSynthesis.getVoices();
    console.log('Available voices:', voices.map(v => `${v.name} (${v.lang})`));

    // Find first English female voice
    const englishFemaleVoice = voices.find(voice => 
      (voice.lang.includes('en-') || voice.lang.includes('en_')) && 
      voice.name.toLowerCase().includes('female')
    );

    if (englishFemaleVoice) {
      console.log('Selected voice:', englishFemaleVoice.name);
      utterance.voice = englishFemaleVoice;
    } else {
      console.warn('No specific female voice found, using default');
    }

    utterance.rate = 0.8; // Slightly slower to ensure complete speech
    utterance.pitch = 1.0;
    utterance.volume = 0.8;

    // Split long text into chunks to prevent interruption
    const splitText = text.match(/[^\.!\?]+[\.!\?]+/g) || [text];

    // Update text based on overview flag
    if (isOverview) {
      setOverviewText(text);
    } else {
      setMessage(text);
    }

    // Speak chunks sequentially
    const speakChunks = async () => {
      for (const chunk of splitText) {
        await new Promise((chunkResolve) => {
          const chunkUtterance = new SpeechSynthesisUtterance(chunk.trim());
          
          if (utterance.voice) {
            chunkUtterance.voice = utterance.voice;
          }
          
          chunkUtterance.rate = utterance.rate;
          chunkUtterance.pitch = utterance.pitch;
          chunkUtterance.volume = utterance.volume;

          chunkUtterance.onstart = () => {
            setIsSpeaking(true);
            console.log('Speaking chunk:', chunk.substring(0, 50) + '...');
          };

          chunkUtterance.onend = () => {
            chunkResolve();
          };

          chunkUtterance.onerror = (error) => {
            console.error('Chunk speech error:', error);
            chunkResolve();
          };

          window.speechSynthesis.speak(chunkUtterance);
        });
      }

      // Final resolution
      setIsSpeaking(false);
      resolve();
    };

    // Start speaking chunks
    speakChunks().catch(error => {
      console.error('Overall speech error:', error);
      setIsSpeaking(false);
      resolve();
    });
  });
};

// Ensure voices are loaded
useEffect(() => {
  const loadVoices = () => {
    const voices = window.speechSynthesis.getVoices();
    console.log('Voices loaded:', voices.map(v => `${v.name} (${v.lang})`));
  };

  if (window.speechSynthesis.onvoiceschanged !== undefined) {
    window.speechSynthesis.onvoiceschanged = loadVoices;
  }

  // Immediate call
  loadVoices();
}, []);
  
  // Add this effect to ensure voice is available
  useEffect(() => {
    const initVoice = () => {
      const voices = window.speechSynthesis.getVoices();
      const hasGoogleUKFemale = voices.some(voice => voice.name === 'Google UK English Female');
      if (!hasGoogleUKFemale) {
        console.error('Google UK English Female voice not available');
      }
    };
  
    window.speechSynthesis.onvoiceschanged = initVoice;
    initVoice();
  
    return () => {
      window.speechSynthesis.onvoiceschanged = null;
    };
  }, []);

  const greetUser = () => {
    const greetingMessage = "Hello! I'm Neo, your AI learning buddy. Let's explore something amazing together!";
    speakResponse(greetingMessage);
  };

  const startListening = useCallback(() => {
    if (isProcessing || isSpeaking) return;
    
    try {
      if (recognitionRef.current) {
        recognitionRef.current.start();
      }
    } catch (error) {
      console.error('Error starting speech recognition:', error);
      setIsListening(false);
    }
  }, [isProcessing, isSpeaking]);

  useEffect(() => {
    let timer;
    if (!isListening && !isProcessing && !isSpeaking) {
      timer = setTimeout(startListening, 2000);
    }
    return () => timer && clearTimeout(timer);
  }, [isListening, isProcessing, isSpeaking, startListening]);

  return (
    <Container>
      <Logo src={logo} alt="NeoNest Logo" />
      <LeftHalf>
        <SplineContainer>
          <canvas 
            ref={canvasRef} 
            style={{ width: '100%', height: '100%' }} 
          />
        </SplineContainer>

        <SpeechBubbleContainer>
      <SpeechBubble $visible={isMessageVisible}>
        {overviewText || message}
      </SpeechBubble>
    </SpeechBubbleContainer>
      </LeftHalf>

      <RightHalf>
  {extractedEntities.map((entity, index) => (
    <EntityCard key={index}>
      {entity.imageUrl ? (
        <EntityImage 
          src={entity.imageUrl} 
          alt="Concept illustration"
          onLoad={() => console.log(`Image loaded`)}
          onError={(e) => {
            console.error(`Failed to load image`);
            e.target.style.display = 'none';
          }}
        />
      ) : (
        <EntityImagePlaceholder>
          <LoadingSpinner />
        </EntityImagePlaceholder>
      )}
      
      <EntityExplanation>{entity.explanation}</EntityExplanation>
    </EntityCard>
  ))}
</RightHalf>

      {cameraActive && (
        <>
          <HiddenVideo
            ref={videoRef}
            playsInline
            autoPlay
            muted
            style={{ display: 'none' }}
          />
          
          {trackingInitialized && (
            <HandTrackingCanvas
              ref={handCanvasRef}
              width={640}
              height={480}
              style={{
                position: 'absolute',
                top: 0,
                right: 0,
                opacity: 0,
                zIndex: -1
              }}
            />
          )}
        </>
      )}
    </Container>
  );
};

export default NeoInteractiveAssistant;