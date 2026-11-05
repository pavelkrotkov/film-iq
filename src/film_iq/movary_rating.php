<?php declare(strict_types=1);

// Movary 0.82.1 application-service bridge; input/output only, no direct SQL.
$container = require '/app/bootstrap.php';
$input = json_decode(stream_get_contents(STDIN), true, 512, JSON_THROW_ON_ERROR);
$user = $container->get(Movary\Domain\User\UserApi::class)->findUserByName($input['username']);
$api = $container->get(Movary\Domain\Movie\MovieApi::class);
$movie = $api->findByTmdbId($input['tmdb_id']);
if ($user === null || $movie === null) {
    throw new RuntimeException('Unknown selected user or film');
}
$rating = Movary\ValueObject\PersonalRating::create($input['rating']);
$api->updateUserRating($movie->getId(), $user->getId(), $rating);
$saved = $api->findUserRating($movie->getId(), $user->getId())?->asInt();
if ($saved !== $input['rating']) {
    throw new RuntimeException('Rating readback failed');
}
echo json_encode(['tmdb_id' => $movie->getTmdbId(), 'rating' => $saved], JSON_THROW_ON_ERROR);
