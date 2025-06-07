<?php
$data = json_decode(file_get_contents("php://input"), true);

if ($data['event'] === "ONIMCOMMANDADD") {
    $command = $data['data']['COMMAND'];
    $dialogId = $data['data']['DIALOG_ID'];
    $botId = $data['data']['BOT_ID'];

    $menu_tree = json_decode(file_get_contents(__DIR__ . "/menu.json"), true);

    if (isset($menu_tree[$command])) {
        $node = $menu_tree[$command];
        $reply = $node['text'];
        $keyboard = [];

        foreach ($node['buttons'] as $button) {
            $keyboard[] = [
                "TYPE" => "BUTTON",
                "TEXT" => $button[0],
                "COMMAND" => $button[1],
                "DISPLAY" => "LINE"
            ];
        }
    } else {
        $reply = "Команда не найдена. Напишите /меню.";
        $keyboard = [];
    }

    $payload = [
        "BOT_ID" => $botId,
        "DIALOG_ID" => $dialogId,
        "MESSAGE" => $reply,
        "KEYBOARD" => $keyboard
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
