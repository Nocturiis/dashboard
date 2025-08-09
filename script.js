document.addEventListener('DOMContentLoaded', () => {
    fetch('annonces_vues.json')
        .then(response => response.json())
        .then(data => {
            const notes = data.map(ad => ad.ai_note);
            const noteCounts = notes.reduce((acc, note) => {
                acc[note] = (acc[note] || 0) + 1;
                return acc;
            }, {});

            document.getElementById('total-annonces').textContent = data.length;

            const ctx = document.getElementById('notesChart').getContext('2d');
            const notesChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(noteCounts),
                    datasets: [{
                        data: Object.values(noteCounts),
                        backgroundColor: [
                            '#dc3545',
                            '#ffc107',
                            '#fd7e14',
                            '#20c997',
                            '#17a2b8'
                        ],
                        hoverOffset: 4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                        },
                        title: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed;
                                    const total = context.dataset.data.reduce((sum, current) => sum + current, 0);
                                    const percentage = ((value / total) * 100).toFixed(2) + '%';
                                    return `Note ${label}: ${value} annonces (${percentage})`;
                                }
                            }
                        }
                    },
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const note = notesChart.data.labels[elements[0].index];
                            displayAdsByNote(data, note);
                        }
                    }
                }
            });

            document.getElementById('show-all').addEventListener('click', () => {
                displayAllAds(data);
            });

            displayAllAds(data);
        })
        .catch(error => console.error('Erreur de chargement du fichier JSON:', error));

    function displayAds(ads) {
        const adsContainer = document.getElementById('ads-container');
        adsContainer.innerHTML = '';
        if (ads.length === 0) {
            adsContainer.innerHTML = '<p style="text-align: center;">Aucune annonce trouvée pour cette note.</p>';
            return;
        }

        ads.forEach(ad => {
            const adCard = document.createElement('div');
            adCard.className = 'ad-card';

            const adTitle = ad.title || 'Titre non disponible';
            const adPrice = ad.price ? `€${ad.price}` : 'Prix non disponible';
            const adDescription = ad.description || 'Description non disponible';
            const adUrl = ad.url || '#';
            const adNote = ad.ai_note ? `Note AI: ${ad.ai_note}/5` : 'Note non disponible';
            const adComment = ad.ai_comment || 'Commentaire non disponible';
            const adYear = ad.year && ad.year !== 'N/A' ? `<span class="meta-item">Année: ${ad.year}</span>` : '';
            const adMileage = ad.mileage && ad.mileage !== 'N/A' ? `<span class="meta-item">Kilométrage: ${ad.mileage}</span>` : '';
            const adFuel = ad.fuel_type && ad.fuel_type !== 'N/A' ? `<span class="meta-item">Carburant: ${ad.fuel_type}</span>` : '';
            const adTransmission = ad.transmission && ad.transmission !== 'N/A' ? `<span class="meta-item">Transmission: ${ad.transmission}</span>` : '';

            adCard.innerHTML = `
                <h3 class="ad-title">${adTitle}</h3>
                <div class="ad-meta">
                    ${adYear}
                    ${adMileage}
                    ${adFuel}
                    ${adTransmission}
                </div>
                <p class="ad-description">${adDescription}</p>
                <div class="ad-price">${adPrice}</div>
                <div class="ad-note">${adNote}</div>
                <div class="ad-comment">${adComment}</div>
                <div class="ad-links">
                    <a href="${adUrl}" target="_blank">Voir l'annonce</a>
                </div>
            `;
            adsContainer.appendChild(adCard);
        });
    }

    function displayAllAds(data) {
        document.getElementById('ads-title').textContent = 'Toutes les annonces';
        displayAds(data);
    }

    function displayAdsByNote(data, note) {
        const filteredAds = data.filter(ad => ad.ai_note == note);
        document.getElementById('ads-title').textContent = `Annonces avec la note ${note}/5`;
        displayAds(filteredAds);
    }
});