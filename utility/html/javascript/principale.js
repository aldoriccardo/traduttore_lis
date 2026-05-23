const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
if (!SpeechRecognition) {
	alert("Il tuo browser non supporta il riconoscimento vocale. Usa Google Chrome.");
} else {
	const recognition = new SpeechRecognition();
	recognition.lang = 'it-IT';
	recognition.continuous = true; 
	recognition.interimResults = false;

	const btnStart = document.getElementById('btn-start');
	const btnStop = document.getElementById('btn-stop');
	const statusDiv = document.getElementById('stato-registrazione');
	const textarea = document.getElementById('testo-riconosciuto');
	
	const boxPlayer = document.getElementById('box-player');
	const videoPlayer = document.getElementById('video-player');
	const wordLabel = document.getElementById('word-label');
	const bannerInt = document.getElementById('banner-int');

	let modalitaContinuaAttiva = false;
	let playlistVideo = [];
	let indiceCorrente = 0;
	let attoreGlobale = "Angela";
	let tentatoFallbackCorrente = false; 

	function aggiornaSfondoPersonaggio() {
		const attoreSelezionato = document.querySelector('input[name="attore_scelto"]:checked').value;
		videoPlayer.poster = `immagini/${attoreSelezionato.toLowerCase()}.png`;
		console.log('Sfondo aggiornato con l anteprima di: ${attoreSelezionato}');
	}

	document.querySelectorAll('input[name="attore_scelto"]').forEach(radio => {
		radio.addEventListener('change', () => {
			aggiornaSfondoPersonaggio();
			attoreGlobale = radio.value;
		});
	});

	// Avvio iniziale sfondo
	aggiornaSfondoPersonaggio();

	btnStart.addEventListener('click', () => {
		modalitaContinuaAttiva = true;
		bannerInt.style.display = "none";
		tentaAccensioneMicrofono();
	});

	btnStop.addEventListener('click', () => {
		modalitaContinuaAttiva = false;
		recognition.stop();
		bannerInt.style.display = "none";
		videoPlayer.pause();
		videoPlayer.src = ""; 
		aggiornaSfondoPersonaggio(); 
		wordLabel.innerText = "PRONTO";
		statusDiv.innerText = "Sistema Arrestato e resettato.";
		statusDiv.style.color = "#dc3545";
	});

	function tentaAccensioneMicrofono() {
		if (!modalitaContinuaAttiva) return;
		try {
			recognition.start();
		} catch (e) {
			console.log("Il microfono era già in ascolto.");
		}
	}

	recognition.onstart = () => {
		statusDiv.innerText = "?? In ascolto continuo... Parla liberamente!";
		statusDiv.style.color = "#28a745";
	};

	recognition.onend = () => {
		if (modalitaContinuaAttiva && !videoPlayer.currentTime) {
			tentaAccensioneMicrofono();
		}
	};

	recognition.onresult = (event) => {
		const t_indice = event.resultIndex;
		const fraseTrascritto = event.results[t_indice][0].transcript.trim();
		
		textarea.value = fraseTrascritto;
		console.log("Frase intercettata: ", fraseTrascritto);

		recognition.stop();
		elaboraETraduciInLIS(fraseTrascritto);
	};

	function elaboraETraduciInLIS(frase) {
		attoreGlobale = document.querySelector('input[name="attore_scelto"]:checked').value;
		statusDiv.innerText = `? Elaborazione LIS con Python...`;
		statusDiv.style.color = "#007bff";
		bannerInt.style.display = "none";

		fetch('http://127.0.0.1:5000/traduci', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ frase: frase, attore: attoreGlobale })
		})
		.then(response => {
			if (!response.ok) throw new Error("Risposta ko dal server");
			return response.json();
		})
		.then(data => {
			if (data.tipo_frase === "INTERROGATIVA") bannerInt.style.display = "block";

			playlistVideo = data.playlist_lis;
			indiceCorrente = 0;

			if (playlistVideo.length > 0) {
				riproduciPlaylist();
			} else {
				riattivaAscoltoAutomatico();
			}
		})
		.catch(error => {
			console.error("Errore connessione Python:", error);
			statusDiv.innerText = "? ERRORE: Controlla che il Server Python sia ACCESO!";
			statusDiv.style.color = "#dc3545";
			modalitaContinuaAttiva = false;
			recognition.stop();
		});
	}

	function riproduciPlaylist() {
		if (playlistVideo.length === 0) return;

		if (indiceCorrente >= playlistVideo.length) {
			riattivaAscoltoAutomatico();
			return;
		}

		tentatoFallbackCorrente = false; 
		const nodoCorrente = playlistVideo[indiceCorrente];
		let cartellaPersonaggio = (attoreGlobale === "Angela") ? "personaggioFemminile" : "personaggioMaschile";
		let base_url = `http://localhost/mioWeb/Siti%20Invalidi/LIS_Linguaggio_dei_Segni/vocabolario/${cartellaPersonaggio}/vocaboli/`;
		
		let nomeFileVideo = nodoCorrente.percorso_video.split('/').pop();
		let urlVideoFinale = base_url + nomeFileVideo;

		wordLabel.innerText = nodoCorrente.lemma_lis.toUpperCase();
		statusDiv.innerText = `Segno: ${nodoCorrente.parola_originale}`;
		statusDiv.style.color = "#007bff";

		videoPlayer.src = urlVideoFinale;
		videoPlayer.load();
		videoPlayer.play().catch(err => { avanzaPlaylist(); });
	}

	function avanzaPlaylist() { indiceCorrente++; riproduciPlaylist(); }
	videoPlayer.onended = () => { avanzaPlaylist(); };

	videoPlayer.onerror = () => {
		console.warn(`Video non trovato all indirizzo: ${videoPlayer.src}`);
		if (!tentatoFallbackCorrente) {
			tentatoFallbackCorrente = true;
			let cartellaPersonaggio = (attoreGlobale === "Angela") ? "personaggioFemminile" : "personaggioMaschile";
			let base_url = `http://localhost/mioWeb/Siti%20Invalidi/LIS_Linguaggio_dei_Segni/vocabolario/${cartellaPersonaggio}/vocaboli/`;
			let urlFallback = base_url + "parola-non-trovata.mp4";
			
			console.log(`Carico il video di ripiego automatico: ${urlFallback}`);
			wordLabel.innerText = "NON TROVATO ??";
			
			videoPlayer.src = urlFallback;
			videoPlayer.load();
			videoPlayer.play().catch(err => { setTimeout(avanzaPlaylist, 500); });
		} else {
			avanzaPlaylist();
		}
	};

	function riattivaAscoltoAutomatico() {
		bannerInt.style.display = "none";
		aggiornaSfondoPersonaggio(); 
		wordLabel.innerText = "PRONTO";
		if (modalitaContinuaAttiva) {
			tentaAccensioneMicrofono();
		}
	}
}