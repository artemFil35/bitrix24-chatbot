<?php
$data = json_decode(file_get_contents("php://input"), true);

if ($data['event'] === "ONIMBOTMESSAGEADD") {
    $message = mb_strtolower($data['data']['PARAMS']['MESSAGE']);
    $dialogId = $data['data']['PARAMS']['DIALOG_ID'];
    $botId = $data['data']['BOT_ID'];

    $reply = "Извините, я вас не понял. Напишите 'помощь'.";

    if (strpos($message, 'помощь') !== false) {
        $reply = "👋 Я ваш помощник! Вот, что я могу:\n\n".
                 "- Написать HR: 'hr'\n".
                 "- Когда сдать отчет: 'отчет'\n".
                 "- IT поддержка: 'саппорт'\n";
    } elseif (strpos($message, 'hr') !== false) {
        $reply = "📞 Контакт HR: hr@company.com";
    } elseif (strpos($message, 'отчет') !== false) {
        $reply = "📅 Сдача отчетов до 15 числа каждого месяца.";
    } elseif (strpos($message, 'саппорт') !== false) {
        $reply = "🛠 Поддержка: support@company.com";
    }

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
