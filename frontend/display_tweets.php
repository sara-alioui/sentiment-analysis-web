<?php
$resultsFile = __DIR__ . '/data/results.json';

// Debug : Afficher le chemin du fichier (à désactiver en production)
// echo "<pre>Chemin du fichier : " . htmlspecialchars($resultsFile) . "</pre>";

if (file_exists($resultsFile)) {
    $data = json_decode(file_get_contents($resultsFile), true);
    
    if (json_last_error() !== JSON_ERROR_NONE) {
        echo '<div class="error">Erreur de décodage JSON : ' . json_last_error_msg() . '</div>';
        exit;
    }

    echo '<div class="sentiment-stats">';
    echo '<h2>Statistiques</h2>';
    
    // Comptage des sentiments
    $stats = [
        'positif' => 0,
        'neutre' => 0,
        'negatif' => 0
    ];
    
    foreach ($data as $tweet) {
        $stats[$tweet['sentiment']]++;
    }
    
    echo '<div class="stats-grid">';
    echo '<div class="stat-box positif">Positifs: ' . $stats['positif'] . '</div>';
    echo '<div class="stat-box neutre">Neutres: ' . $stats['neutre'] . '</div>';
    echo '<div class="stat-box negatif">Négatifs: ' . $stats['negatif'] . '</div>';
    echo '</div>'; // .stats-grid
    echo '</div>'; // .sentiment-stats

    // Affichage des tweets
    echo '<div class="tweets-container">';
    echo '<h2>Tweets analysés</h2>';
    echo '<div class="tweets-list">';
    
    foreach ($data as $tweet) {
        echo '<div class="tweet ' . htmlspecialchars($tweet['sentiment']) . '">';
        echo '<div class="tweet-content">' . htmlspecialchars($tweet['original_tweet']) . '</div>';
        echo '<div class="tweet-details">';
        echo '<span class="sentiment">' . ucfirst($tweet['sentiment']) . '</span>';
        echo '<span class="score">Score: ' . round($tweet['score']['compound'], 2) . '</span>';
        echo '</div>'; // .tweet-details
        echo '</div>'; // .tweet
    }
    
    echo '</div>'; // .tweets-list
    echo '</div>'; // .tweets-container

} else {
    echo '<div class="error">';
    echo '<p>Aucun résultat trouvé. Veuillez :</p>';
    echo '<ol>';
    echo '<li>Exécuter d\'abord le script Python analyzer.py</li>';
    echo '<li>Vérifier que le fichier results.json existe dans le dossier data/</li>';
    echo '</ol>';
    echo '</div>';
}
?>