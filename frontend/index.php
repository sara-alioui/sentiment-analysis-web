<?php
// Security measures
ini_set('display_errors', 1); // Activer l'affichage des erreurs pour déboguer
error_reporting(E_ALL);
session_start();

// Define constants
define('DATA_PATH', 'data/results.json');

// Helper functions
function getSafeHtml($str) {
    return htmlspecialchars($str, ENT_QUOTES, 'UTF-8');
}

// Load data with error handling
function loadSentimentData() {
    if (!file_exists(DATA_PATH)) {
        return [
            'error' => 'Aucune donnée trouvée. Lancez d\'abord l\'analyse depuis l\'application Python.',
            'data' => null
        ];
    }

    $jsonData = @file_get_contents(DATA_PATH);
    if ($jsonData === false) {
        return [
            'error' => 'Impossible de lire le fichier de données.',
            'data' => null
        ];
    }

    $data = @json_decode($jsonData, true);
    if ($data === null && json_last_error() !== JSON_ERROR_NONE) {
        return [
            'error' => 'Erreur de lecture des données JSON: ' . json_last_error_msg(),
            'data' => null
        ];
    }

    if (!is_array($data) || empty($data)) {
        return [
            'error' => 'Aucune donnée valide trouvée dans le fichier.',
            'data' => []
        ];
    }

    return [
        'error' => null,
        'data' => $data
    ];
}

// Calculate statistics
function calculateStats($data) {
    $stats = ['positif' => 0, 'neutre' => 0, 'negatif' => 0];
    $total = 0;
    
    if (is_array($data)) {
        foreach ($data as $tweet) {
            if (isset($tweet['sentiment']) && array_key_exists($tweet['sentiment'], $stats)) {
                $stats[$tweet['sentiment']]++;
                $total++;
            }
        }
    }
    
    $percentages = [
        'positif' => $total > 0 ? round(($stats['positif']/$total)*100, 1) : 0,
        'neutre' => $total > 0 ? round(($stats['neutre']/$total)*100, 1) : 0,
        'negatif' => $total > 0 ? round(($stats['negatif']/$total)*100, 1) : 0
    ];
    
    return [
        'stats' => $stats,
        'total' => $total,
        'percentages' => $percentages
    ];
}

// Extract keywords
function extractKeywords($data, $limit = 10) {
    $keywords = [];
    $stopwords = ['avec', 'pour', 'dans', 'cette', 'votre', 'notre', 'mais', 'donc', 'quand', 'alors'];
    
    if (is_array($data)) {
        foreach ($data as $tweet) {
            if (isset($tweet['tweet'])) {
                $text = preg_replace('/[^\p{L}\p{N}\s]/u', '', mb_strtolower($tweet['tweet'], 'UTF-8'));
                $words = preg_split('/\s+/', $text, -1, PREG_SPLIT_NO_EMPTY);
                
                foreach ($words as $word) {
                    if (mb_strlen($word, 'UTF-8') > 3 && !in_array($word, $stopwords)) {
                        if (!isset($keywords[$word])) $keywords[$word] = 0;
                        $keywords[$word]++;
                    }
                }
            }
        }
    }
    
    arsort($keywords);
    return array_slice($keywords, 0, $limit, true);
}

// Pour simplifier, nous n'avons plus besoin de cette variable
// $currentSearch = isset($_GET['topic']) ? $_GET['topic'] : '';

// Load data and process it
$result = loadSentimentData();
$data = $result['data'];
$error = $result['error'];

// Calculate statistics if we have data
if ($data !== null) {
    $statsResult = calculateStats($data);
    $stats = $statsResult['stats'];
    $total = $statsResult['total'];
    $percentages = $statsResult['percentages'];
    $topKeywords = extractKeywords($data);
} else {
    $stats = ['positif' => 0, 'neutre' => 0, 'negatif' => 0];
    $total = 0;
    $percentages = ['positif' => 0, 'neutre' => 0, 'negatif' => 0];
    $topKeywords = [];
}

// Convertir les statistiques en JSON pour le JavaScript
$statsJson = json_encode([
    'counts' => $stats,
    'percentages' => $percentages
]);
?>
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <meta name="description" content="SAZAfeels - Analyse de sentiments Twitter">
    <meta name="robots" content="noindex, nofollow">
    <title>SAZAfeels - Analyse de Sentiments Twitter</title>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
    <!-- Chargement de Chart.js directement depuis CDN avec version spécifique -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <style>
        :root {
            --color-background: #D9EDF8; /* Light blue background from logo */
            --color-primary: #0F5B94; /* Dark blue from logo */
            --color-text: #1F3B54; /* Darker version of the blue */
            --color-white: #FFFFFF;
            --color-border: rgba(15, 91, 148, 0.2);
            
            --color-negative: #F25C54; /* Red from logo */
            --color-neutral: #FFCA3A; /* Yellow from logo */
            --color-positive: #8AC926; /* Green from logo */
            
            --font-family: 'Montserrat', sans-serif;
            
            --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.1);
            --shadow-md: 0 4px 8px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 8px 16px rgba(0, 0, 0, 0.1);
            
            --border-radius-sm: 8px;
            --border-radius-md: 12px;
            --border-radius-lg: 20px;
            --border-radius-xl: 30px;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: var(--font-family);
            background-color: var(--color-background);
            color: var(--color-text);
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
        }
        
        .logo-container {
            margin-bottom: 20px;
            display: flex;
            justify-content: center;
        }
        
        .logo-img {
            width: 180px;
            height: 180px;
        }
        
        .error-box {
            background-color: #FFE8E6;
            border-left: 4px solid var(--color-negative);
            color: #D32F2F;
            padding: 16px;
            border-radius: var(--border-radius-sm);
            margin-bottom: 20px;
            display: flex;
            align-items: center;
        }
        
        .error-icon {
            font-size: 20px;
            margin-right: 10px;
        }
        
        .stats-container {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 24px;
            margin-bottom: 40px;
        }
        
        .stat-card {
            background: var(--color-white);
            border-radius: var(--border-radius-md);
            padding: 24px;
            box-shadow: var(--shadow-md);
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            border: 2px solid;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: var(--shadow-lg);
        }
        
        .stat-card.negatif { border-color: var(--color-negative); }
        .stat-card.neutre { border-color: var(--color-neutral); }
        .stat-card.positif { border-color: var(--color-positive); }
        
        .stat-icon {
            width: 60px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: var(--border-radius-sm);
            margin-bottom: 16px;
        }
        
        .stat-card.negatif .stat-icon { background-color: var(--color-negative); }
        .stat-card.neutre .stat-icon { background-color: var(--color-neutral); }
        .stat-card.positif .stat-icon { background-color: var(--color-positive); }
        
        .stat-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 12px;
        }
        
        .stat-value {
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        
        .stat-card.negatif .stat-value { color: var(--color-negative); }
        .stat-card.neutre .stat-value { color: var(--color-neutral); }
        .stat-card.positif .stat-value { color: var(--color-positive); }
        
        .stat-percentage {
            font-size: 16px;
            opacity: 0.8;
        }
        
        .tab-container {
            display: flex;
            background: var(--color-white);
            border-radius: var(--border-radius-md);
            padding: 5px;
            margin-bottom: 30px;
            box-shadow: var(--shadow-sm);
            overflow: hidden;
        }
        
        .tab {
            flex: 1;
            padding: 12px 20px;
            text-align: center;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            border-radius: var(--border-radius-sm);
            color: var(--color-text);
        }
        
        .tab.active {
            background-color: var(--color-primary);
            color: var(--color-white);
        }
        
        .tab-panel {
            display: none;
        }
        
        .tab-panel.active {
            display: block;
            animation: fadeIn 0.4s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .card {
            background: var(--color-white);
            border-radius: var(--border-radius-md);
            padding: 24px;
            box-shadow: var(--shadow-md);
            margin-bottom: 24px;
        }
        
        .card-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--color-border);
        }
        
        .card-icon {
            width: 40px;
            height: 40px;
            background: var(--color-primary);
            border-radius: var(--border-radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 16px;
        }
        
        .card-title {
            font-size: 20px;
            font-weight: 600;
            color: var(--color-primary);
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 24px;
            margin-bottom: 24px;
        }
        
        .chart-container {
            position: relative;
            height: 300px;
            width: 100%;
            min-height: 300px;
        }
        
        .chart-container canvas {
            width: 100% !important;
            height: 100% !important;
        }
        
        .tweets-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 24px;
            margin-bottom: 24px;
        }
        
        .tweet {
            background: var(--color-white);
            border-radius: var(--border-radius-md);
            padding: 20px;
            box-shadow: var(--shadow-md);
            border-top: 5px solid;
        }
        
        .tweet.positif { border-top-color: var(--color-positive); }
        .tweet.neutre { border-top-color: var(--color-neutral); }
        .tweet.negatif { border-top-color: var(--color-negative); }
        
        .tweet-text {
            margin-bottom: 16px;
            line-height: 1.5;
        }
        
        .tweet-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .sentiment-badge {
            display: inline-flex;
            align-items: center;
            padding: 6px 12px;
            border-radius: var(--border-radius-sm);
            font-size: 14px;
            font-weight: 600;
        }
        
        .sentiment-badge.positif { 
            background-color: var(--color-positive); 
            color: var(--color-white);
        }
        
        .sentiment-badge.neutre { 
            background-color: var(--color-neutral); 
            color: var(--color-text);
        }
        
        .sentiment-badge.negatif { 
            background-color: var(--color-negative); 
            color: var(--color-white);
        }
        
        .sentiment-icon {
            margin-right: 6px;
        }
        
        .score-badge {
            padding: 4px 10px;
            border-radius: var(--border-radius-sm);
            font-size: 14px;
            background: rgba(15, 91, 148, 0.1);
            color: var(--color-primary);
        }
        
        .keywords-container {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 20px;
        }
        
        .keyword {
            padding: 8px 16px;
            background: var(--color-white);
            border-radius: var(--border-radius-xl);
            font-size: 14px;
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--color-border);
        }
        
        .keyword-count {
            display: inline-block;
            margin-left: 5px;
            font-weight: 600;
            color: var(--color-primary);
        }
        
        .insights-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 24px;
        }
        
        .insight-item {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--color-border);
        }
        
        .insight-item:last-child {
            margin-bottom: 0;
            padding-bottom: 0;
            border-bottom: none;
        }
        
        .insight-icon {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: var(--color-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 16px;
            flex-shrink: 0;
        }
        
        .insight-content {
            flex: 1;
        }
        
        .insight-label {
            font-size: 14px;
            color: var(--color-text);
            opacity: 0.7;
            margin-bottom: 4px;
        }
        
        .insight-value {
            font-size: 22px;
            font-weight: 700;
            color: var(--color-primary);
        }
        
        /* History Section Styles */
        .history-card {
            background: var(--color-white);
            border-radius: var(--border-radius-md);
            padding: 24px;
            box-shadow: var(--shadow-md);
            margin-bottom: 24px;
        }
        
        .history-list {
            list-style-type: none;
            padding: 0;
        }
        
        .history-item {
            padding: 12px 16px;
            border-bottom: 1px solid var(--color-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background-color 0.2s ease;
        }
        
        .history-item:last-child {
            border-bottom: none;
        }
        
        .history-item:hover {
            background-color: rgba(15, 91, 148, 0.05);
        }
        
        .history-term {
            font-weight: 600;
            color: var(--color-primary);
        }
        
        .history-meta {
            font-size: 14px;
            color: var(--color-text);
            opacity: 0.7;
        }
        
        .history-count {
            background: var(--color-primary);
            color: white;
            border-radius: 50%;
            width: 28px;
            height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: 600;
        }
        
        .empty-history {
            padding: 20px;
            text-align: center;
            color: var(--color-text);
            opacity: 0.7;
        }
        
        @media (max-width: 768px) {
            .stats-container {
                grid-template-columns: 1fr;
            }
            
            .charts-grid,
            .tweets-grid,
            .insights-grid {
                grid-template-columns: 1fr;
            }
            
            .tab-container {
                flex-wrap: wrap;
            }
            
            .tab {
                flex-basis: 100%;
                margin-bottom: 5px;
            }
            
            .tweet-footer {
                flex-direction: column;
                align-items: flex-start;
            }
            
            .header {
                padding: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="logo-container">
                <!-- SAZAfeels Logo - Only keep this -->
                <img src="hhhh.png" alt="SAZAfeels Logo" class="logo-img">
            </div>
        </header>
        
        <?php if ($error !== null): ?>
        <div class="error-box">
            <span class="error-icon">⚠</span>
            <?php echo getSafeHtml($error); ?>
        </div>
        <?php endif; ?>
        
        <?php if ($total > 0): ?>
        <!-- Statistics Cards -->
        <div class="stats-container">
            <div class="stat-card negatif">
                <div class="stat-icon">
                    <svg viewBox="0 0 24 24" fill="#1F3B54">
                        <path d="M12 2C6.47 2 2 6.47 2 12s4.47 10 10 10 10-4.47 10-10S17.53 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm3.59-13.41L12 10.17l-3.59-3.58L7 8l5 5 5-5-1.41-1.41z"/>
                    </svg>
                </div>
                <div class="stat-title">Tweets Négatifs</div>
                <div class="stat-value"><?php echo number_format($stats['negatif'], 0, ',', ' '); ?></div>
                <div class="stat-percentage"><?php echo $percentages['negatif']; ?>% du total</div>
            </div>
            
            <div class="stat-card neutre">
                <div class="stat-icon">
                    <svg viewBox="0 0 24 24" fill="#1F3B54">
                        <path d="M9 14h6v1.5H9z"/>
                        <circle cx="15.5" cy="9.5" r="1.5"/>
                        <circle cx="8.5" cy="9.5" r="1.5"/>
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
                    </svg>
                </div>
                <div class="stat-title">Tweets Neutres</div>
                <div class="stat-value"><?php echo number_format($stats['neutre'], 0, ',', ' '); ?></div>
                <div class="stat-percentage"><?php echo $percentages['neutre']; ?>% du total</div>
            </div>
            
            <div class="stat-card positif">
                <div class="stat-icon">
                    <svg viewBox="0 0 24 24" fill="#1F3B54">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm4.5-4.2l-1.1.8-3.4-4.8-3.4 4.8-1.1-.8 4.5-6.3 4.5 6.3z"/>
                    </svg>
                </div>
                <div class="stat-title">Tweets Positifs</div>
                <div class="stat-value"><?php echo number_format($stats['positif'], 0, ',', ' '); ?></div>
                <div class="stat-percentage"><?php echo $percentages['positif']; ?>% du total</div>
            </div>
        </div>
        
        <!-- Tab Navigation -->
        <div class="tab-container">
            <div class="tab active" data-tab="visualisations">Visualisations</div>
            <div class="tab" data-tab="tweets">Tweets</div>
            <div class="tab" data-tab="insights">Insights</div>
        </div>
        
        <!-- Visualisations Tab -->
        <div class="tab-panel active" id="visualisations-panel">
            <div class="charts-grid">
                <div class="card">
                    <div class="card-header">
                        <div class="card-icon">
                            <svg viewBox="0 0 24 24" fill="#FFFFFF">
                                <path d="M11,2V22C5.9,21.5 2,17.2 2,12C2,6.8 5.9,2.5 11,2M13,2V11H22C21.5,6.2 17.8,2.5 13,2M13,13V22C17.7,21.5 21.5,17.8 22,13H13Z" />
                            </svg>
                        </div>
                        <div class="card-title">Répartition des sentiments</div>
                    </div>
                    <div class="chart-container">
                        <canvas id="pieChart"></canvas>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <div class="card-icon">
                            <svg viewBox="0 0 24 24" fill="#FFFFFF">
                                <path d="M22,21H2V3H4V19H22V21M19,15H5V10H19V15M19,8H5V5H19V8Z" />
                            </svg>
                        </div>
                        <div class="card-title">Comparaison des sentiments</div>
                    </div>
                    <div class="chart-container">
                        <canvas id="barChart"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <div class="card-icon">
                    <svg viewBox="0 0 24 24" fill="#FFFFFF">
                            <path d="M3.5,18.49L9.5,12.48L13.5,16.48L22,6.92L20.59,5.5L13.5,13.48L9.5,9.48L2,16.99L3.5,18.49Z" />
                        </svg>
                    </div>
                    <div class="card-title">Tendance des sentiments</div>
                </div>
                <div class="chart-container">
                    <canvas id="lineChart"></canvas>
                </div>
            </div>
        </div>
        
        <!-- Insights Tab -->
        <div class="tab-panel" id="insights-panel">
            <div class="insights-grid">
                <div class="card">
                    <div class="card-header">
                        <div class="card-icon">
                            <svg viewBox="0 0 24 24" fill="#FFFFFF">
                                <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4M7,10L12,15L17,10H7Z" />
                            </svg>
                        </div>
                        <div class="insight-content">
                            <div class="insight-label">Sentiment dominant</div>
                            <div class="insight-value">
                                <?php 
                                    if ($total > 0) {
                                        echo ucfirst(getSafeHtml(array_search(max($stats), $stats)));
                                    } else {
                                        echo 'Non disponible';
                                    }
                                ?>
                            </div>
                        </div>
                    </div>
                    
                    <div class="insight-item">
                        <div class="insight-icon">
                            <svg viewBox="0 0 24 24" fill="#FFFFFF">
                                <path d="M12,3C7.58,3 4,4.79 4,7C4,9.21 7.58,11 12,11C16.42,11 20,9.21 20,7C20,4.79 16.42,3 12,3M4,9V12C4,14.21 7.58,16 12,16C16.42,16 20,14.21 20,12V9C20,11.21 16.42,13 12,13C7.58,13 4,11.21 4,9M4,14V17C4,19.21 7.58,21 12,21C16.42,21 20,19.21 20,17V14C20,16.21 16.42,18 12,18C7.58,18 4,16.21 4,14Z" />
                            </svg>
                        </div>
                        <div class="insight-content">
                            <div class="insight-label">Ratio positif/négatif</div>
                            <div class="insight-value">
                                <?php 
                                    if ($stats['negatif'] > 0) {
                                        echo round($stats['positif'] / $stats['negatif'], 1);
                                    } else if ($stats['positif'] > 0) {
                                        echo '∞'; // Infinity symbol when no negative tweets
                                    } else {
                                        echo 'N/A';
                                    }
                                ?>
                            </div>
                        </div>
                    </div>
                    
                    <div class="insight-item">
                        <div class="insight-icon">
                            <svg viewBox="0 0 24 24" fill="#FFFFFF">
                                <path d="M19 3H5C3.9 3 3 3.9 3 5V19C3 20.1 3.9 21 5 21H19C20.1 21 21 20.1 21 19V5C21 3.9 20.1 3 19 3M9 17H7V10H9V17M13 17H11V7H13V17M17 17H15V13H17V17Z" />
                            </svg>
                        </div>
                        <div class="insight-content">
                        <div class="insight-label">Écart entre sentiments extrêmes</div>
                            <div class="insight-value">
                                <?php echo abs($stats['positif'] - $stats['negatif']); ?> tweets
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <div class="card-icon">
                            <svg viewBox="0 0 24 24" fill="#FFFFFF">
                                <path d="M5.5,9A1.5,1.5 0 0,0 7,7.5A1.5,1.5 0 0,0 5.5,6A1.5,1.5 0 0,0 4,7.5A1.5,1.5 0 0,0 5.5,9M17.41,11.58C17.77,11.94 18,12.44 18,13C18,13.55 17.78,14.05 17.41,14.41L12.41,19.41C12.05,19.77 11.55,20 11,20C10.45,20 9.95,19.78 9.58,19.41L2.59,12.42C2.22,12.05 2,11.55 2,11V6C2,4.89 2.89,4 4,4H9C9.55,4 10.05,4.22 10.41,4.58L17.41,11.58M13.54,5.71L14.54,4.71L21.41,11.58C21.78,11.94 22,12.45 22,13C22,13.55 21.78,14.05 21.42,14.41L16.04,19.79L15.04,18.79L20.75,13L13.54,5.71Z" />
                            </svg>
                        </div>
                        <div class="card-title">Mots-clés Populaires</div>
                    </div>
                    
                    <div class="keywords-container">
                        <?php if (!empty($topKeywords)): ?>
                            <?php foreach($topKeywords as $word => $count): ?>
                                <div class="keyword">
                                    <?php echo getSafeHtml($word); ?>
                                    <span class="keyword-count"><?php echo intval($count); ?></span>
                                </div>
                            <?php endforeach; ?>
                        <?php else: ?>
                            <div>Aucun mot-clé disponible</div>
                        <?php endif; ?>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Tweets Tab -->
        <div class="tab-panel" id="tweets-panel">
            <div class="tweets-grid">
                <?php if (!empty($data)): ?>
                    <?php 
                    $sampleTweets = array_slice($data, 0, min(6, count($data)));
                    foreach($sampleTweets as $tweet): 
                    ?>
                        <?php 
                            $sentimentClass = isset($tweet['sentiment']) ? getSafeHtml($tweet['sentiment']) : '';
                            
                            $icon = '';
                            switch($tweet['sentiment'] ?? '') {
                                case 'positif': $icon = 'smile'; break;
                                case 'neutre': $icon = 'neutral'; break;
                                case 'negatif': $icon = 'sad'; break;
                                default: $icon = 'question'; break;
                            }
                        ?>
                        <div class="tweet <?php echo $sentimentClass; ?>">
                            <div class="tweet-text">
                                <?php echo isset($tweet['tweet']) ? getSafeHtml($tweet['tweet']) : 'Texte non disponible'; ?>
                            </div>
                            <div class="tweet-footer">
                                <div class="sentiment-badge <?php echo $sentimentClass; ?>">
                                    <?php if($icon == 'smile'): ?>
                                        <svg class="sentiment-icon" width="16" height="16" viewBox="0 0 24 24">
                                            <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm4.5-4.2l-1.1.8-3.4-4.8-3.4 4.8-1.1-.8 4.5-6.3 4.5 6.3z"/>
                                        </svg>
                                    <?php elseif($icon == 'neutral'): ?>
                                        <svg class="sentiment-icon" width="16" height="16" viewBox="0 0 24 24">
                                            <path fill="currentColor" d="M9 14h6v1.5H9z"/>
                                            <circle fill="currentColor" cx="15.5" cy="9.5" r="1.5"/>
                                            <circle fill="currentColor" cx="8.5" cy="9.5" r="1.5"/>
                                            <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
                                        </svg>
                                    <?php elseif($icon == 'sad'): ?>
                                        <svg class="sentiment-icon" width="16" height="16" viewBox="0 0 24 24">
                                            <path fill="currentColor" d="M12 2C6.47 2 2 6.47 2 12s4.47 10 10 10 10-4.47 10-10S17.53 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm3.59-13.41L12 10.17l-3.59-3.58L7 8l5 5 5-5-1.41-1.41z"/>
                                        </svg>
                                    <?php else: ?>
                                        <svg class="sentiment-icon" width="16" height="16" viewBox="0 0 24 24">
                                            <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-7h2v5h-2v-5zm0-4h2v2h-2V9z"/>
                                        </svg>
                                    <?php endif; ?>
                                    <?php echo isset($tweet['sentiment']) ? ucfirst(getSafeHtml($tweet['sentiment'])) : 'Non défini'; ?>
                                </div>
                                
                                <?php if (isset($tweet['score']['compound'])): ?>
                                    <div class="score-badge">
                                        Score: <?php echo round(floatval($tweet['score']['compound']), 2); ?>
                                    </div>
                                <?php endif; ?>
                            </div>
                        </div>
                    <?php endforeach; ?>
                <?php else: ?>
                    <div class="tweet">
                        <div class="tweet-text">Aucun tweet disponible pour analyse.</div>
                    </div>
                <?php endif; ?>
            </div>
        </div>
        <?php else: ?>
            <div class="card">
                <div class="card-header">
                    <div class="card-icon">
                        <svg viewBox="0 0 24 24" fill="#FFFFFF">
                            <path d="M13,13H11V7H13M13,17H11V15H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z" />
                        </svg>
                    </div>
                    <div class="card-title">Information</div>
                </div>
                <p>Aucune donnée d'analyse de sentiment n'est disponible. Veuillez lancer l'analyse depuis l'application Python.</p>
            </div>
        <?php endif; ?>
    </div>

<script>
// Stocker les statistiques PHP en variables JavaScript
const statsData = <?php echo $statsJson; ?>;
console.log("Données chargées:", statsData);

// Configuration générale
const sentimentLabels = ['Positif', 'Neutre', 'Négatif'];
const sentimentColors = ['#8AC926', '#FFCA3A', '#F25C54'];

// Attendre que le document soit complètement chargé
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM chargé");
    
    // Gestion des onglets
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            tabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));
            const targetPanel = document.getElementById(this.dataset.tab + '-panel');
            if (targetPanel) {
                targetPanel.classList.add('active');
            }
        });
    });
    
    // Initialiser les graphiques
    createCharts();
});

// Fonction pour créer les graphiques
function createCharts() {
    // Vérifier que Chart.js est chargé
    if (typeof Chart === 'undefined') {
        console.error("Chart.js n'est pas chargé");
        return;
    }
    
    // Récupérer les données pour les graphiques
    const chartData = {
        counts: [
            statsData.counts.positif || 0,
            statsData.counts.neutre || 0,
            statsData.counts.negatif || 0
        ],
        percentages: [
            statsData.percentages.positif || 0,
            statsData.percentages.neutre || 0,
            statsData.percentages.negatif || 0
        ]
    };
    
    console.log("Création des graphiques avec les données:", chartData);

    // Graphique camembert
    const pieCtx = document.getElementById('pieChart');
    if (pieCtx) {
        new Chart(pieCtx, {
            type: 'doughnut',
            data: {
                labels: sentimentLabels,
                datasets: [{
                    data: chartData.percentages,
                    backgroundColor: sentimentColors,
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.label}: ${context.raw}%`;
                            }
                        }
                    }
                }
            }
        });
    }

    // Graphique à barres
    const barCtx = document.getElementById('barChart');
    if (barCtx) {
        new Chart(barCtx, {
            type: 'bar',
            data: {
                labels: sentimentLabels,
                datasets: [{
                    label: 'Nombre de tweets',
                    data: chartData.counts,
                    backgroundColor: sentimentColors,
                    borderRadius: 6,
                    maxBarThickness: 60
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    // Données simulées pour la tendance
    function generateTrendData(total, days = 7) {
        const result = [];
        for (let i = 0; i < days; i++) {
            result.push(Math.round((total / days) * (0.7 + Math.random() * 0.6)));
        }
        return result;
    }

    const days = ['Jour 1', 'Jour 2', 'Jour 3', 'Jour 4', 'Jour 5', 'Jour 6', 'Jour 7'];

    // Graphique linéaire
    const lineCtx = document.getElementById('lineChart');
    if (lineCtx) {
        new Chart(lineCtx, {
            type: 'line',
            data: {
                labels: days,
                datasets: [
                    {
                        label: 'Positif',
                        data: generateTrendData(chartData.counts[0]),
                        borderColor: sentimentColors[0],
                        backgroundColor: 'rgba(138, 201, 38, 0.1)',
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'Neutre',
                        data: generateTrendData(chartData.counts[1]),
                        borderColor: sentimentColors[1],
                        backgroundColor: 'rgba(255, 202, 58, 0.1)',
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'Négatif',
                        data: generateTrendData(chartData.counts[2]),
                        borderColor: sentimentColors[2],
                        backgroundColor: 'rgba(242, 92, 84, 0.1)',
                        tension: 0.3,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    console.log("Tous les graphiques ont été créés");
}
</script>
</body>
</html>