const newman = require('newman');

// Initial config part
let config = {
    collection: 'collection.json',
    delayRequest: Number(process.env.DELAY_REQUEST),
};

try {
    environment = require('environment.json');
    config = {
        ...config,
        environment
    };
} catch (e) {
	console.log('catched error: ' + e);
    if (!e instanceof Error || e.code == ! "MODULE_NOT_FOUND") {
        throw e;
    }
}

/** Makes the newman call awaitable */
function run() {
    newman.run(config, (err) => {
		console.log('running loop ...');
        if (err) throw err;
        setTimeout(run, process.env.DELAY_ROUNDS);
    });
}

// Never end process of running
console.log('Everything setup, starting with loop');
console.log(config);
console.log(process.env.DELAY_ROUNDS)
run();
