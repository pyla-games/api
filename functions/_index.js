export function onRequestGet() {
    console.log('ROOT PATH HIT!');
    return new Response('Root path works!', {
        status: 200,
        headers: { 'Content-Type': 'text/plain' }
    });
}
