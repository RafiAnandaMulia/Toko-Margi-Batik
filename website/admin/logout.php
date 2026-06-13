<?php

require_once __DIR__ . '/../config/session.php';

destroySession();

header(
    'Location: /BATIK_CLASSIFICATION_SYSTEM/website/admin/login.php?logout=1'
);

exit;