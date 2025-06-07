<?php
$data = json_decode(file_get_contents("php://input"), true);

// ==== OpenAI GPT-Функция ====
function askChatGPT($messageText) {
    $apiKey = getenv("OPENAI_API_KEY"); // Ключ из переменной окружения
    if (!$apiKey) return "❗ Ошибка: API-ключ OpenAI не задан.";

    $url = 'https://api.openai.com/v1/chat/completions';

    $data = [
        'model' => 'gpt-4',
        'messages' => [
            ['role' => 'system', 'content' => 'Ты — корпоративный помощник. Отвечай понятно и лаконично.'],
            ['role' => 'user', 'content' => $messageText]
        ],
        'temperature' => 0.7
    ];

    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Authorization: Bearer ' . $apiKey,
        'Content-Type: application/json'
    ]);

    $response = curl_exec($ch);
    curl_close($ch);

    $result = json_decode($response, true);
    return $result['choices'][0]['message']['content'] ?? 'Ошибка генерации ответа.';
}

// ==== Обработка входящих сообщений от Bitrix24 ====
if ($data['event'] === "ONIMBOTMESSAGEADD") {
    $message = $data['data']['PARAMS']['MESSAGE'];
    $dialogId = $data['data']['PARAMS']['DIALOG_ID'];
    $botId = $data['data']['BOT_ID'];

    $reply = askChatGPT($message);

    $payload = [
        "BOT_ID" => $botId,
        "DIALOG_ID" => $dialogId,
        "MESSAGE" => $reply
    ];

    $url = "https://tdroks.bitrix24.ru/rest/1/n70eln7e90vnou3d/imbot.message.add.json";

    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($payload));
    curl_setopt($ch, CURLOPT_HTTPHEADER, ["Content-Type: application/json"]);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_exec($ch);
    curl_close($ch);
}

echo json_encode(["result" => "OK"]);
?>
