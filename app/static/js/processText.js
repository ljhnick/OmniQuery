function processText() {
    const textInput = document.getElementById('userInputQuery').value;
    
    fetch('/process_text', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({text: textInput}),
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('displayText').innerText = data.processed_text;
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}