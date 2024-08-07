function processQuery() {
    const query = document.getElementById('userInputQuery').value;
    const badgeSearching = document.getElementById('badgeSearching');
    const badgeFinished = document.getElementById('badgeFinished');
    const badgeLoading = document.getElementById('badgeLoading');
    const badgeLoaded = document.getElementById('badgeLoaded');
    badgeLoading.style.display = 'none';
    badgeLoaded.style.display = 'none';
    badgeSearching.style.display = 'block';
    badgeFinished.style.display = 'none';
    
    fetch('/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({text: query}),
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('displayText').innerText = data.answer;
        document.getElementById('timeCostText').innerText = `Time cost: ${data.time_cost}s`;
        displayImages(data.images);
        badgeSearching.style.display = 'none';
        badgeFinished.style.display = 'block';
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

function displayImages(images) {
    const container = document.getElementById('image-container');
    container.innerHTML = '';  // Clear existing images
    images.forEach(imageBase64 => {
        const img = document.createElement('img');
        img.src = `data:image/jpeg;base64,${imageBase64}`;
        img.alt = "Retrieved image";
        img.style.height = '400px';  // Adjust the size as needed
        container.appendChild(img);
    });
}

function init() {
    const badgeLoading = document.getElementById('badgeLoading');
    const badgeLoaded = document.getElementById('badgeLoaded');
    badgeLoading.style.display = 'block';
    
    fetch('/init', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({})  // Sending an empty JSON object
    })
    .then(response => response.json())
    .then(data => {
        console.log('Response:', data);
        badgeLoading.style.display = 'none';
        badgeLoaded.style.display = 'block';
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}