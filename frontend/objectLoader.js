/**
 * 3D Object Loader for Feng Shui Room Designer
 * Creates simple 3D representations of furniture and decor items
 */

class ObjectLoader {
    constructor(scene) {
        this.scene = scene;
        this.objectTemplates = this.createObjectTemplates();
    }

    createObjectTemplates() {
        return {
            // Furniture
            bed: () => this.createBed(),
            sofa: () => this.createSofa(),
            desk: () => this.createDesk(),
            table: () => this.createTable(),
            chair: () => this.createChair(),
            wardrobe: () => this.createWardrobe(),
            bookshelf: () => this.createBookshelf(),
            tv: () => this.createTV(),
            
            // Decor
            mirror: () => this.createMirror(),
            painting: () => this.createPainting(),
            clock: () => this.createClock(),
            vase: () => this.createVase(),
            rug: () => this.createRug(),
            curtain: () => this.createCurtain(),
            window: () => this.createWindow(),
            door: () => this.createDoor(),
            fountain: () => this.createFountain(),
            crystals: () => this.createCrystals(),
            
            // Plants
            bamboo: () => this.createBamboo(),
            plant: () => this.createPlant(),
            bonsai: () => this.createBonsai(),
            flowers: () => this.createFlowers(),
            
            // Lighting
            lamp: () => this.createLamp(),
            chandelier: () => this.createChandelier(),
            candle: () => this.createCandle()
        };
    }

    loadObject(type, fengShuiData) {
        const createFunc = this.objectTemplates[type];
        if (!createFunc) {
            console.warn(`Object type ${type} not found`);
            return this.createDefaultBox(type);
        }

        const object = createFunc();
        object.userData.type = type;
        object.userData.fengShui = fengShuiData;
        return object;
    }

    // Furniture creators
    createBed() {
        const group = new THREE.Group();
        
        // Modern low platform base (dark gray upholstered)
        const baseGeometry = new THREE.BoxGeometry(2.2, 0.35, 1.7);
        const darkGrayMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x3a3a3a,
            roughness: 0.85,
            metalness: 0.05
        });
        const base = new THREE.Mesh(baseGeometry, darkGrayMaterial);
        base.position.y = 0.175;
        base.castShadow = true;
        group.add(base);
        
        // Mattress with white/cream bedding
        const mattressGeometry = new THREE.BoxGeometry(2.0, 0.3, 1.6);
        const beddingMaterial = new THREE.MeshStandardMaterial({ 
            color: 0xf8f8f8,
            roughness: 0.9,
            metalness: 0.0
        });
        const mattress = new THREE.Mesh(mattressGeometry, beddingMaterial);
        mattress.position.y = 0.5;
        mattress.castShadow = true;
        group.add(mattress);
        
        // Modern thick padded headboard (dark gray upholstered)
        const headboardGeometry = new THREE.BoxGeometry(2.2, 0.9, 0.15);
        const headboardMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x404040,
            roughness: 0.8,
            metalness: 0.05
        });
        const headboard = new THREE.Mesh(headboardGeometry, headboardMaterial);
        headboard.position.set(0, 0.8, -0.85);
        headboard.castShadow = true;
        group.add(headboard);
        
        // Large white pillows (back row - 2 pillows)
        const largePillowGeometry = new THREE.BoxGeometry(0.5, 0.2, 0.35);
        const whitePillowMaterial = new THREE.MeshStandardMaterial({ 
            color: 0xfafafa,
            roughness: 0.85,
            metalness: 0.0
        });
        
        const whitePillow1 = new THREE.Mesh(largePillowGeometry, whitePillowMaterial);
        whitePillow1.position.set(-0.45, 0.65, -0.55);
        whitePillow1.rotation.x = -0.15;
        whitePillow1.castShadow = true;
        group.add(whitePillow1);
        
        const whitePillow2 = new THREE.Mesh(largePillowGeometry, whitePillowMaterial);
        whitePillow2.position.set(0.45, 0.65, -0.55);
        whitePillow2.rotation.x = -0.15;
        whitePillow2.castShadow = true;
        group.add(whitePillow2);
        
        // Taupe/gray accent pillows (middle row - 2 pillows)
        const accentPillowGeometry = new THREE.BoxGeometry(0.38, 0.16, 0.28);
        const taupePillowMaterial = new THREE.MeshStandardMaterial({ 
            color: 0xa89f94,
            roughness: 0.88,
            metalness: 0.0
        });
        
        const taupePillow1 = new THREE.Mesh(accentPillowGeometry, taupePillowMaterial);
        taupePillow1.position.set(-0.4, 0.75, -0.4);
        taupePillow1.rotation.x = -0.1;
        taupePillow1.castShadow = true;
        group.add(taupePillow1);
        
        const taupePillow2 = new THREE.Mesh(accentPillowGeometry, taupePillowMaterial);
        taupePillow2.position.set(0.4, 0.75, -0.4);
        taupePillow2.rotation.x = -0.1;
        taupePillow2.castShadow = true;
        group.add(taupePillow2);
        
        // Brown center accent pillow
        const centerPillowGeometry = new THREE.BoxGeometry(0.32, 0.14, 0.24);
        const brownPillowMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x8b6f47,
            roughness: 0.9,
            metalness: 0.0
        });
        
        const centerPillow = new THREE.Mesh(centerPillowGeometry, brownPillowMaterial);
        centerPillow.position.set(0, 0.8, -0.35);
        centerPillow.rotation.x = -0.08;
        centerPillow.castShadow = true;
        group.add(centerPillow);
        
        // Dark checkered throw blanket at foot of bed
        const throwGeometry = new THREE.BoxGeometry(1.9, 0.08, 0.6);
        
        // Create checkered pattern texture for throw
        const throwCanvas = document.createElement('canvas');
        throwCanvas.width = 256;
        throwCanvas.height = 256;
        const throwCtx = throwCanvas.getContext('2d');
        
        const checkSize = 16;
        for (let y = 0; y < 256; y += checkSize) {
            for (let x = 0; x < 256; x += checkSize) {
                const isLight = ((x / checkSize) + (y / checkSize)) % 2 === 0;
                throwCtx.fillStyle = isLight ? '#4a4a4a' : '#2a2a2a';
                throwCtx.fillRect(x, y, checkSize, checkSize);
            }
        }
        
        const throwTexture = new THREE.CanvasTexture(throwCanvas);
        throwTexture.wrapS = THREE.RepeatWrapping;
        throwTexture.wrapT = THREE.RepeatWrapping;
        
        const throwMaterial = new THREE.MeshStandardMaterial({ 
            map: throwTexture,
            roughness: 0.92,
            metalness: 0.0
        });
        
        const throwBlanket = new THREE.Mesh(throwGeometry, throwMaterial);
        throwBlanket.position.set(0, 0.68, 0.4);
        throwBlanket.castShadow = true;
        group.add(throwBlanket);
        
        return group;
    }

    createSofa() {
        const group = new THREE.Group();
        
        // Modern sofa with realistic proportions
        const sofaMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x708090,
            roughness: 0.85,
            metalness: 0.05
        });
        
        // Main seat cushion
        const seatGeometry = new THREE.BoxGeometry(2.0, 0.4, 0.9);
        const seat = new THREE.Mesh(seatGeometry, sofaMaterial);
        seat.position.y = 0.45;
        seat.castShadow = true;
        group.add(seat);
        
        // Back cushions
        const backCushionGeometry = new THREE.BoxGeometry(2.0, 0.7, 0.25);
        const backCushion = new THREE.Mesh(backCushionGeometry, sofaMaterial);
        backCushion.position.set(0, 0.75, -0.325);
        backCushion.castShadow = true;
        group.add(backCushion);
        
        // Armrests (padded)
        const armrestGeometry = new THREE.BoxGeometry(0.2, 0.6, 0.9);
        const leftArmrest = new THREE.Mesh(armrestGeometry, sofaMaterial);
        leftArmrest.position.set(-1.0, 0.6, 0);
        leftArmrest.castShadow = true;
        group.add(leftArmrest);
        
        const rightArmrest = new THREE.Mesh(armrestGeometry, sofaMaterial);
        rightArmrest.position.set(1.0, 0.6, 0);
        rightArmrest.castShadow = true;
        group.add(rightArmrest);
        
        // Base frame
        const baseGeometry = new THREE.BoxGeometry(2.1, 0.15, 0.95);
        const baseMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x3a3a3a,
            roughness: 0.7
        });
        const base = new THREE.Mesh(baseGeometry, baseMaterial);
        base.position.y = 0.15;
        base.castShadow = true;
        group.add(base);
        
        // Decorative throw pillows
        const pillowGeometry = new THREE.BoxGeometry(0.35, 0.12, 0.35);
        const pillowMaterial = new THREE.MeshStandardMaterial({ 
            color: 0xd2b48c,
            roughness: 0.9
        });
        
        const pillow1 = new THREE.Mesh(pillowGeometry, pillowMaterial);
        pillow1.position.set(-0.5, 0.7, 0);
        pillow1.rotation.y = 0.3;
        pillow1.castShadow = true;
        group.add(pillow1);
        
        const pillow2 = new THREE.Mesh(pillowGeometry, pillowMaterial);
        pillow2.position.set(0.5, 0.7, 0);
        pillow2.rotation.y = -0.3;
        pillow2.castShadow = true;
        group.add(pillow2);
        
        return group;
    }

    createDesk() {
        const group = new THREE.Group();
        
        // Modern desk with realistic wood texture
        const woodMaterial = new THREE.MeshStandardMaterial({ 
            color: 0xc19a6b,
            roughness: 0.6,
            metalness: 0.1
        });
        
        // Desktop
        const topGeometry = new THREE.BoxGeometry(1.5, 0.05, 0.8);
        const top = new THREE.Mesh(topGeometry, woodMaterial);
        top.position.y = 0.75;
        top.castShadow = true;
        group.add(top);
        
        // Drawer unit (right side)
        const drawerGeometry = new THREE.BoxGeometry(0.4, 0.5, 0.7);
        const drawer = new THREE.Mesh(drawerGeometry, woodMaterial);
        drawer.position.set(0.5, 0.4, 0);
        drawer.castShadow = true;
        group.add(drawer);
        
        // Drawer handles
        const handleMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x404040,
            roughness: 0.3,
            metalness: 0.8
        });
        const handleGeometry = new THREE.CylinderGeometry(0.01, 0.01, 0.15, 8);
        
        for (let i = 0; i < 3; i++) {
            const handle = new THREE.Mesh(handleGeometry, handleMaterial);
            handle.rotation.z = Math.PI / 2;
            handle.position.set(0.5, 0.2 + (i * 0.2), 0.36);
            group.add(handle);
        }
        
        // Legs (modern metal legs)
        const legGeometry = new THREE.CylinderGeometry(0.02, 0.02, 0.75, 12);
        const legMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x2c2c2c,
            roughness: 0.4,
            metalness: 0.7
        });
        const positions = [
            [-0.7, 0.375, -0.35],
            [-0.7, 0.375, 0.35]
        ];
        
        positions.forEach(pos => {
            const leg = new THREE.Mesh(legGeometry, legMaterial);
            leg.position.set(...pos);
            leg.castShadow = true;
            group.add(leg);
        });
        
        return group;
    }

    createTable() {
        const group = new THREE.Group();
        
        // Rectangular wooden tabletop with realistic wood grain
        const topGeometry = new THREE.BoxGeometry(2.0, 0.06, 1.0);
        
        // Create wood grain texture
        const woodCanvas = document.createElement('canvas');
        woodCanvas.width = 512;
        woodCanvas.height = 512;
        const woodCtx = woodCanvas.getContext('2d');
        
        // Base wood color (oak/light brown)
        const baseColor = '#b8936f';
        woodCtx.fillStyle = baseColor;
        woodCtx.fillRect(0, 0, 512, 512);
        
        // Add wood grain lines
        for (let i = 0; i < 80; i++) {
            const y = Math.random() * 512;
            const opacity = 0.05 + Math.random() * 0.1;
            woodCtx.strokeStyle = `rgba(90, 60, 30, ${opacity})`;
            woodCtx.lineWidth = 1 + Math.random() * 2;
            woodCtx.beginPath();
            woodCtx.moveTo(0, y);
            for (let x = 0; x < 512; x += 20) {
                const wave = Math.sin(x / 40) * 3;
                woodCtx.lineTo(x, y + wave);
            }
            woodCtx.stroke();
        }
        
        const woodTexture = new THREE.CanvasTexture(woodCanvas);
        woodTexture.wrapS = THREE.RepeatWrapping;
        woodTexture.wrapT = THREE.RepeatWrapping;
        woodTexture.repeat.set(2, 1);
        
        const woodMaterial = new THREE.MeshStandardMaterial({ 
            map: woodTexture,
            color: 0xffffff,
            roughness: 0.6,
            metalness: 0.1
        });
        const top = new THREE.Mesh(topGeometry, woodMaterial);
        top.position.y = 0.76;
        top.castShadow = true;
        top.receiveShadow = true;
        group.add(top);
        
        // Black metal legs (modern H-frame design)
        const metalMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x1a1a1a,
            roughness: 0.4,
            metalness: 0.8
        });
        
        // Vertical legs
        const verticalLegGeometry = new THREE.BoxGeometry(0.05, 0.73, 0.05);
        const legPositions = [
            [-0.85, 0.365, -0.4],
            [-0.85, 0.365, 0.4],
            [0.85, 0.365, -0.4],
            [0.85, 0.365, 0.4]
        ];
        
        legPositions.forEach(pos => {
            const leg = new THREE.Mesh(verticalLegGeometry, metalMaterial);
            leg.position.set(...pos);
            leg.castShadow = true;
            group.add(leg);
        });
        
        // Horizontal support beams
        const longBeamGeometry = new THREE.BoxGeometry(1.75, 0.05, 0.05);
        const shortBeamGeometry = new THREE.BoxGeometry(0.05, 0.05, 0.85);
        
        // Long beams (connecting front and back)
        const leftBeam = new THREE.Mesh(longBeamGeometry, metalMaterial);
        leftBeam.position.set(0, 0.15, -0.4);
        group.add(leftBeam);
        
        const rightBeam = new THREE.Mesh(longBeamGeometry, metalMaterial);
        rightBeam.position.set(0, 0.15, 0.4);
        group.add(rightBeam);
        
        // Short beams (connecting left and right)
        const frontShortBeam = new THREE.Mesh(shortBeamGeometry, metalMaterial);
        frontShortBeam.position.set(-0.85, 0.15, 0);
        group.add(frontShortBeam);
        
        const backShortBeam = new THREE.Mesh(shortBeamGeometry, metalMaterial);
        backShortBeam.position.set(0.85, 0.15, 0);
        group.add(backShortBeam);
        
        return group;
    }

    createChair() {
        const group = new THREE.Group();
        
        // Brown leather/fabric upholstery material
        const upholsteryMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x8b5a3c,
            roughness: 0.8,
            metalness: 0.05
        });
        
        // Seat cushion
        const seatGeometry = new THREE.BoxGeometry(0.45, 0.08, 0.48);
        const seat = new THREE.Mesh(seatGeometry, upholsteryMaterial);
        seat.position.y = 0.48;
        seat.castShadow = true;
        group.add(seat);
        
        // Curved backrest with channel tufting
        const backrestGeometry = new THREE.BoxGeometry(0.42, 0.55, 0.08);
        const backrest = new THREE.Mesh(backrestGeometry, upholsteryMaterial);
        backrest.position.set(0, 0.75, -0.22);
        backrest.rotation.x = -0.1; // Slight backward tilt
        backrest.castShadow = true;
        group.add(backrest);
        
        // Add vertical channel tufting lines to backrest
        const tuftingMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x6b4226,
            roughness: 0.9
        });
        
        for (let i = 0; i < 7; i++) {
            const tuftGeometry = new THREE.BoxGeometry(0.015, 0.5, 0.02);
            const tuft = new THREE.Mesh(tuftGeometry, tuftingMaterial);
            const xPos = -0.18 + (i * 0.06);
            tuft.position.set(xPos, 0.75, -0.18);
            tuft.rotation.x = -0.1;
            group.add(tuft);
        }
        
        // Black metal legs
        const legMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x0a0a0a,
            roughness: 0.3,
            metalness: 0.9
        });
        
        const legGeometry = new THREE.CylinderGeometry(0.018, 0.015, 0.48, 12);
        const legPositions = [
            [-0.16, 0.24, -0.18],
            [0.16, 0.24, -0.18],
            [-0.16, 0.24, 0.18],
            [0.16, 0.24, 0.18]
        ];
        
        // Gold/brass tips material
        const brassMaterial = new THREE.MeshStandardMaterial({ 
            color: 0xd4af37,
            roughness: 0.2,
            metalness: 0.95
        });
        
        legPositions.forEach(pos => {
            // Main leg
            const leg = new THREE.Mesh(legGeometry, legMaterial);
            leg.position.set(...pos);
            leg.castShadow = true;
            group.add(leg);
            
            // Brass tip
            const tipGeometry = new THREE.CylinderGeometry(0.02, 0.018, 0.04, 12);
            const tip = new THREE.Mesh(tipGeometry, brassMaterial);
            tip.position.set(pos[0], 0.02, pos[2]);
            group.add(tip);
        });
        
        return group;
    }

    createWardrobe() {
        const group = new THREE.Group();
        
        const woodMaterial = new THREE.MeshStandardMaterial({ 
            color: 0xa0826d,
            roughness: 0.7,
            metalness: 0.1
        });
        
        // Main cabinet body
        const geometry = new THREE.BoxGeometry(1.4, 2.2, 0.6);
        const wardrobe = new THREE.Mesh(geometry, woodMaterial);
        wardrobe.position.y = 1.1;
        wardrobe.castShadow = true;
        group.add(wardrobe);
        
        // Left door
        const doorGeometry = new THREE.BoxGeometry(0.68, 2.1, 0.05);
        const doorMaterial = new THREE.MeshStandardMaterial({ 
            color: 0xb89968,
            roughness: 0.6,
            metalness: 0.1
        });
        const leftDoor = new THREE.Mesh(doorGeometry, doorMaterial);
        leftDoor.position.set(-0.35, 1.1, 0.32);
        leftDoor.castShadow = true;
        group.add(leftDoor);
        
        // Right door
        const rightDoor = new THREE.Mesh(doorGeometry, doorMaterial);
        rightDoor.position.set(0.35, 1.1, 0.32);
        rightDoor.castShadow = true;
        group.add(rightDoor);
        
        // Door handles (modern metal)
        const handleMaterial = new THREE.MeshStandardMaterial({ 
            color: 0xc0c0c0,
            roughness: 0.2,
            metalness: 0.9
        });
        const handleGeometry = new THREE.CylinderGeometry(0.015, 0.015, 0.12, 8);
        
        const leftHandle = new THREE.Mesh(handleGeometry, handleMaterial);
        leftHandle.position.set(-0.15, 1.1, 0.35);
        group.add(leftHandle);
        
        const rightHandle = new THREE.Mesh(handleGeometry, handleMaterial);
        rightHandle.position.set(0.55, 1.1, 0.35);
        group.add(rightHandle);
        
        // Base
        const baseGeometry = new THREE.BoxGeometry(1.45, 0.1, 0.65);
        const base = new THREE.Mesh(baseGeometry, woodMaterial);
        base.position.y = 0.05;
        base.castShadow = true;
        group.add(base);
        
        return group;
    }

    createBookshelf() {
        const group = new THREE.Group();
        
        // Light natural wood material (beech/oak)
        const woodMaterial = new THREE.MeshStandardMaterial({ 
            color: 0xe8c4a0,
            roughness: 0.65,
            metalness: 0.05
        });
        
        // Vertical support legs (4 legs - 2 per side)
        const legGeometry = new THREE.CylinderGeometry(0.02, 0.02, 1.8, 16);
        const legPositions = [
            [-0.52, 0.9, -0.15],
            [-0.52, 0.9, 0.15],
            [0.52, 0.9, -0.15],
            [0.52, 0.9, 0.15]
        ];
        
        legPositions.forEach(pos => {
            const leg = new THREE.Mesh(legGeometry, woodMaterial);
            leg.position.set(...pos);
            leg.castShadow = true;
            group.add(leg);
        });
        
        // 5-tier shelves with ladder-style increasing depth
        const shelfHeights = [0.3, 0.65, 1.0, 1.35, 1.7];
        const shelfDepths = [0.28, 0.30, 0.32, 0.34, 0.36]; // Slightly increasing depth
        
        for (let i = 0; i < 5; i++) {
            // Main shelf surface
            const shelfGeometry = new THREE.BoxGeometry(1.1, 0.03, shelfDepths[i]);
            const shelf = new THREE.Mesh(shelfGeometry, woodMaterial);
            shelf.position.y = shelfHeights[i];
            shelf.castShadow = true;
            shelf.receiveShadow = true;
            group.add(shelf);
            
            // Curved front edge/lip
            const edgeGeometry = new THREE.CylinderGeometry(0.025, 0.025, 1.1, 16);
            const edge = new THREE.Mesh(edgeGeometry, woodMaterial);
            edge.rotation.z = Math.PI / 2;
            edge.position.set(0, shelfHeights[i] + 0.025, shelfDepths[i] / 2);
            group.add(edge);
            
            // Back support bar
            const backBarGeometry = new THREE.CylinderGeometry(0.02, 0.02, 1.1, 12);
            const backBar = new THREE.Mesh(backBarGeometry, woodMaterial);
            backBar.rotation.z = Math.PI / 2;
            backBar.position.set(0, shelfHeights[i], -shelfDepths[i] / 2);
            group.add(backBar);

            // Add books with varied heights and colors on each shelf
            const bookColors = [0x3e4a89, 0x8a3f2f, 0x2f6f5f, 0xc4a24f, 0x5b4b8a, 0x7a6a52, 0x2f4f6b];
            const bookDepth = Math.max(0.16, shelfDepths[i] - 0.08);
            const startX = -0.45;
            const bookCount = i < 2 ? 8 : 6;

            for (let j = 0; j < bookCount; j++) {
                const width = 0.045 + ((j + i) % 3) * 0.01;
                const height = 0.16 + ((j + i * 2) % 4) * 0.04;
                const color = bookColors[(j + i) % bookColors.length];

                const bookMaterial = new THREE.MeshStandardMaterial({
                    color,
                    roughness: 0.78,
                    metalness: 0.02
                });

                const book = new THREE.Mesh(
                    new THREE.BoxGeometry(width, height, bookDepth),
                    bookMaterial
                );

                book.position.set(
                    startX + j * 0.075,
                    shelfHeights[i] + 0.02 + (height / 2),
                    0
                );
                book.castShadow = true;
                book.receiveShadow = true;

                // Slight tilt variation for natural look
                book.rotation.z = ((j % 2 === 0 ? 1 : -1) * 0.02) + (i * 0.002);
                group.add(book);
            }
        }
        
        return group;
    }

    createTV() {
        const group = new THREE.Group();

        const frameMaterial = new THREE.MeshStandardMaterial({
            color: 0x111317,
            roughness: 0.45,
            metalness: 0.35
        });

        // Thin outer frame
        const frame = new THREE.Mesh(new THREE.BoxGeometry(1.28, 0.76, 0.045), frameMaterial);
        frame.position.y = 0.86;
        frame.castShadow = true;
        frame.receiveShadow = true;
        group.add(frame);

        // Screen panel with subtle gradient reflection
        const screenCanvas = document.createElement('canvas');
        screenCanvas.width = 512;
        screenCanvas.height = 320;
        const sctx = screenCanvas.getContext('2d');

        const grad = sctx.createLinearGradient(0, 0, 512, 320);
        grad.addColorStop(0, '#192430');
        grad.addColorStop(0.5, '#0d141d');
        grad.addColorStop(1, '#131d28');
        sctx.fillStyle = grad;
        sctx.fillRect(0, 0, 512, 320);

        sctx.fillStyle = 'rgba(170, 210, 255, 0.12)';
        sctx.beginPath();
        sctx.ellipse(140, 90, 160, 56, -0.35, 0, Math.PI * 2);
        sctx.fill();

        sctx.fillStyle = 'rgba(255, 255, 255, 0.05)';
        sctx.fillRect(0, 250, 512, 40);

        const screenTexture = new THREE.CanvasTexture(screenCanvas);
        const screen = new THREE.Mesh(
            new THREE.PlaneGeometry(1.18, 0.66),
            new THREE.MeshStandardMaterial({
                map: screenTexture,
                roughness: 0.14,
                metalness: 0.08
            })
        );
        screen.position.set(0, 0.87, 0.0235);
        group.add(screen);

        // Rear chassis gives realistic thickness profile
        const back = new THREE.Mesh(
            new THREE.BoxGeometry(1.08, 0.58, 0.09),
            new THREE.MeshStandardMaterial({ color: 0x0f1218, roughness: 0.55, metalness: 0.25 })
        );
        back.position.set(0, 0.86, -0.03);
        back.castShadow = true;
        group.add(back);

        // Bottom trim with small logo nub
        const trim = new THREE.Mesh(
            new THREE.BoxGeometry(1.18, 0.024, 0.02),
            new THREE.MeshStandardMaterial({ color: 0x232833, roughness: 0.38, metalness: 0.42 })
        );
        trim.position.set(0, 0.52, 0.02);
        group.add(trim);

        const logoNub = new THREE.Mesh(
            new THREE.BoxGeometry(0.06, 0.01, 0.008),
            new THREE.MeshStandardMaterial({ color: 0x48525f, roughness: 0.4, metalness: 0.4 })
        );
        logoNub.position.set(0, 0.505, 0.024);
        group.add(logoNub);

        // Stand neck
        const neck = new THREE.Mesh(
            new THREE.BoxGeometry(0.08, 0.22, 0.045),
            new THREE.MeshStandardMaterial({ color: 0x252a31, roughness: 0.4, metalness: 0.52 })
        );
        neck.position.set(0, 0.39, -0.01);
        neck.castShadow = true;
        group.add(neck);

        // V-shaped feet (common modern TV stand style)
        const footMaterial = new THREE.MeshStandardMaterial({ color: 0x20252c, roughness: 0.42, metalness: 0.55 });
        const leftFoot = new THREE.Mesh(new THREE.BoxGeometry(0.36, 0.02, 0.12), footMaterial);
        leftFoot.position.set(-0.23, 0.02, 0.01);
        leftFoot.rotation.y = 0.32;
        leftFoot.castShadow = true;
        leftFoot.receiveShadow = true;
        group.add(leftFoot);

        const rightFoot = new THREE.Mesh(new THREE.BoxGeometry(0.36, 0.02, 0.12), footMaterial);
        rightFoot.position.set(0.23, 0.02, 0.01);
        rightFoot.rotation.y = -0.32;
        rightFoot.castShadow = true;
        rightFoot.receiveShadow = true;
        group.add(rightFoot);
        
        return group;
    }

    // Decor creators
    createMirror() {
        const group = new THREE.Group();

        // Dimensions
        const outerW = 0.86;
        const outerH = 1.28;
        const rail = 0.07;
        const depth = 0.05;
        const centerY = 1.0;

        const frameMaterial = new THREE.MeshStandardMaterial({
            color: 0x454c56,
            roughness: 0.22,
            metalness: 0.72
        });
        const bevelMaterial = new THREE.MeshStandardMaterial({
            color: 0x8f9aaa,
            roughness: 0.18,
            metalness: 0.65
        });

        // Build frame rails (looks more like a true frame than one solid block)
        const topRail = new THREE.Mesh(new THREE.BoxGeometry(outerW, rail, depth), frameMaterial);
        topRail.position.set(0, centerY + (outerH / 2) - (rail / 2), 0);
        group.add(topRail);

        const bottomRail = new THREE.Mesh(new THREE.BoxGeometry(outerW, rail, depth), frameMaterial);
        bottomRail.position.set(0, centerY - (outerH / 2) + (rail / 2), 0);
        group.add(bottomRail);

        const sideH = outerH - (rail * 2);
        const leftRail = new THREE.Mesh(new THREE.BoxGeometry(rail, sideH, depth), frameMaterial);
        leftRail.position.set(-(outerW / 2) + (rail / 2), centerY, 0);
        group.add(leftRail);

        const rightRail = new THREE.Mesh(new THREE.BoxGeometry(rail, sideH, depth), frameMaterial);
        rightRail.position.set((outerW / 2) - (rail / 2), centerY, 0);
        group.add(rightRail);

        // Inner bevel rails
        const innerW = outerW - (rail * 1.45);
        const innerH = outerH - (rail * 1.45);
        const innerRail = 0.018;
        const bevelZ = 0.014;

        const bevelTop = new THREE.Mesh(new THREE.BoxGeometry(innerW, innerRail, 0.02), bevelMaterial);
        bevelTop.position.set(0, centerY + (innerH / 2), bevelZ);
        group.add(bevelTop);

        const bevelBottom = new THREE.Mesh(new THREE.BoxGeometry(innerW, innerRail, 0.02), bevelMaterial);
        bevelBottom.position.set(0, centerY - (innerH / 2), bevelZ);
        group.add(bevelBottom);

        const bevelSideH = innerH - (innerRail * 2);
        const bevelLeft = new THREE.Mesh(new THREE.BoxGeometry(innerRail, bevelSideH, 0.02), bevelMaterial);
        bevelLeft.position.set(-(innerW / 2), centerY, bevelZ);
        group.add(bevelLeft);

        const bevelRight = new THREE.Mesh(new THREE.BoxGeometry(innerRail, bevelSideH, 0.02), bevelMaterial);
        bevelRight.position.set((innerW / 2), centerY, bevelZ);
        group.add(bevelRight);

        // Mirror texture with richer reflection cues and edge falloff
        const mirrorCanvas = document.createElement('canvas');
        mirrorCanvas.width = 320;
        mirrorCanvas.height = 512;
        const ctx = mirrorCanvas.getContext('2d');

        const baseGrad = ctx.createLinearGradient(0, 0, 320, 512);
        baseGrad.addColorStop(0, '#f8fcff');
        baseGrad.addColorStop(0.46, '#b7c8d9');
        baseGrad.addColorStop(1, '#e8f0f8');
        ctx.fillStyle = baseGrad;
        ctx.fillRect(0, 0, 320, 512);

        ctx.fillStyle = 'rgba(255,255,255,0.45)';
        ctx.beginPath();
        ctx.ellipse(84, 120, 88, 52, -0.3, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = 'rgba(255,255,255,0.22)';
        ctx.beginPath();
        ctx.ellipse(232, 300, 110, 72, 0.2, 0, Math.PI * 2);
        ctx.fill();

        // Vertical soft reflection band
        const bandGrad = ctx.createLinearGradient(120, 0, 180, 0);
        bandGrad.addColorStop(0, 'rgba(255,255,255,0)');
        bandGrad.addColorStop(0.5, 'rgba(255,255,255,0.18)');
        bandGrad.addColorStop(1, 'rgba(255,255,255,0)');
        ctx.fillStyle = bandGrad;
        ctx.fillRect(90, 0, 110, 512);

        // Edge vignette for depth
        const vignette = ctx.createRadialGradient(160, 256, 120, 160, 256, 270);
        vignette.addColorStop(0, 'rgba(0,0,0,0)');
        vignette.addColorStop(1, 'rgba(40,50,65,0.22)');
        ctx.fillStyle = vignette;
        ctx.fillRect(0, 0, 320, 512);

        const texture = new THREE.CanvasTexture(mirrorCanvas);
        texture.colorSpace = THREE.SRGBColorSpace || texture.colorSpace;

        const mirrorFace = new THREE.Mesh(
            new THREE.PlaneGeometry(0.72, 1.12),
            new THREE.MeshPhysicalMaterial({
                map: texture,
                color: 0xf2f8ff,
                metalness: 1.0,
                roughness: 0.015,
                clearcoat: 1.0,
                clearcoatRoughness: 0.01,
                reflectivity: 1.0,
                side: THREE.DoubleSide
            })
        );
        mirrorFace.position.set(0, centerY, 0.026);
        group.add(mirrorFace);

        // Gloss highlights
        const gloss1 = new THREE.Mesh(
            new THREE.PlaneGeometry(0.11, 1.05),
            new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.2, side: THREE.DoubleSide, blending: THREE.AdditiveBlending })
        );
        gloss1.position.set(-0.22, centerY + 0.02, 0.028);
        gloss1.rotation.z = -0.1;
        group.add(gloss1);

        const gloss2 = new THREE.Mesh(
            new THREE.PlaneGeometry(0.07, 0.58),
            new THREE.MeshBasicMaterial({ color: 0xe8f4ff, transparent: true, opacity: 0.14, side: THREE.DoubleSide, blending: THREE.AdditiveBlending })
        );
        gloss2.position.set(0.19, centerY - 0.12, 0.029);
        gloss2.rotation.z = 0.12;
        group.add(gloss2);

        group.traverse((child) => {
            if (child.isMesh) {
                child.castShadow = true;
                child.receiveShadow = true;
            }
        });
        
        return group;
    }

    createPainting() {
        const group = new THREE.Group();
        
        // Frame
        const frameGeometry = new THREE.BoxGeometry(0.8, 0.6, 0.05);
        const frameMaterial = new THREE.MeshStandardMaterial({ color: 0x8b4513 });
        const frame = new THREE.Mesh(frameGeometry, frameMaterial);
        frame.position.y = 1.5;
        group.add(frame);
        
        // Canvas
        const canvasGeometry = new THREE.BoxGeometry(0.7, 0.5, 0.02);
        const canvasMaterial = new THREE.MeshStandardMaterial({ color: 0x87ceeb });
        const canvas = new THREE.Mesh(canvasGeometry, canvasMaterial);
        canvas.position.set(0, 1.5, 0.03);
        group.add(canvas);
        
        return group;
    }

    createClock() {
        const group = new THREE.Group();

        // 2D wall clock face
        const face = new THREE.Mesh(
            new THREE.CircleGeometry(0.24, 48),
            new THREE.MeshBasicMaterial({ color: 0xf7f8fa, side: THREE.DoubleSide })
        );
        face.position.set(0, 1.5, 0);
        group.add(face);

        // Outer ring
        const ring = new THREE.Mesh(
            new THREE.RingGeometry(0.215, 0.24, 48),
            new THREE.MeshBasicMaterial({ color: 0x2b3138, side: THREE.DoubleSide })
        );
        ring.position.set(0, 1.5, 0.001);
        group.add(ring);

        // Hour markers
        const markerMaterial = new THREE.MeshBasicMaterial({ color: 0x2b3138, side: THREE.DoubleSide });
        for (let i = 0; i < 12; i++) {
            const marker = new THREE.Mesh(new THREE.PlaneGeometry(0.012, i % 3 === 0 ? 0.04 : 0.024), markerMaterial);
            const a = (i / 12) * Math.PI * 2;
            marker.position.set(
                Math.cos(a) * 0.18,
                1.5 + Math.sin(a) * 0.18,
                0.002
            );
            marker.rotation.z = a;
            group.add(marker);
        }

        // Clock hands
        const hourHand = new THREE.Mesh(
            new THREE.PlaneGeometry(0.014, 0.09),
            new THREE.MeshBasicMaterial({ color: 0x1f2933, side: THREE.DoubleSide })
        );
        hourHand.position.set(-0.025, 1.53, 0.003);
        hourHand.rotation.z = 0.8;
        group.add(hourHand);

        const minuteHand = new THREE.Mesh(
            new THREE.PlaneGeometry(0.01, 0.14),
            new THREE.MeshBasicMaterial({ color: 0x111827, side: THREE.DoubleSide })
        );
        minuteHand.position.set(0.03, 1.535, 0.0035);
        minuteHand.rotation.z = -0.55;
        group.add(minuteHand);

        // Center cap
        const center = new THREE.Mesh(
            new THREE.CircleGeometry(0.014, 20),
            new THREE.MeshBasicMaterial({ color: 0x111827, side: THREE.DoubleSide })
        );
        center.position.set(0, 1.5, 0.004);
        group.add(center);
        
        return group;
    }

    createVase() {
        const group = new THREE.Group();

        const vaseScale = 1.2; // Slightly larger than default

        // Main ceramic body profile (x = radius, y = height)
        const profile = [
            new THREE.Vector2(0.02 * vaseScale, 0.0 * vaseScale),
            new THREE.Vector2(0.08 * vaseScale, 0.02 * vaseScale),
            new THREE.Vector2(0.11 * vaseScale, 0.08 * vaseScale),
            new THREE.Vector2(0.12 * vaseScale, 0.16 * vaseScale),
            new THREE.Vector2(0.10 * vaseScale, 0.26 * vaseScale),
            new THREE.Vector2(0.07 * vaseScale, 0.34 * vaseScale),
            new THREE.Vector2(0.06 * vaseScale, 0.40 * vaseScale),
            new THREE.Vector2(0.08 * vaseScale, 0.46 * vaseScale)
        ];

        const bodyMaterial = new THREE.MeshStandardMaterial({
            color: 0x5f85c9,
            roughness: 0.2,
            metalness: 0.05
        });

        const body = new THREE.Mesh(new THREE.LatheGeometry(profile, 48), bodyMaterial);
        body.position.y = 0.01;
        body.castShadow = true;
        body.receiveShadow = true;
        group.add(body);

        // Top rim ring
        const rim = new THREE.Mesh(
            new THREE.TorusGeometry(0.078 * vaseScale, 0.008 * vaseScale, 14, 40),
            new THREE.MeshStandardMaterial({ color: 0x8fb0e6, roughness: 0.18, metalness: 0.08 })
        );
        rim.rotation.x = Math.PI / 2;
        rim.position.y = 0.47 * vaseScale;
        group.add(rim);

        // Bottom foot ring
        const foot = new THREE.Mesh(
            new THREE.TorusGeometry(0.07 * vaseScale, 0.006 * vaseScale, 12, 36),
            new THREE.MeshStandardMaterial({ color: 0x4568a8, roughness: 0.25, metalness: 0.06 })
        );
        foot.rotation.x = Math.PI / 2;
        foot.position.y = 0.02 * vaseScale;
        group.add(foot);

        // Subtle glossy highlight strip for ceramic feel
        const gloss = new THREE.Mesh(
            new THREE.PlaneGeometry(0.05 * vaseScale, 0.28 * vaseScale),
            new THREE.MeshBasicMaterial({
                color: 0xd8e8ff,
                transparent: true,
                opacity: 0.2,
                side: THREE.DoubleSide,
                blending: THREE.AdditiveBlending
            })
        );
        gloss.position.set(0.055 * vaseScale, 0.27 * vaseScale, 0.075 * vaseScale);
        gloss.rotation.y = -0.5;
        group.add(gloss);
        
        return group;
    }

    createRug() {
        const group = new THREE.Group();

        // Woven texture with central medallion and border to avoid a flat color block look.
        const textureCanvas = document.createElement('canvas');
        textureCanvas.width = 768;
        textureCanvas.height = 1024;
        const tctx = textureCanvas.getContext('2d');

        // Base weave tone
        tctx.fillStyle = '#8f342e';
        tctx.fillRect(0, 0, textureCanvas.width, textureCanvas.height);

        // Fine weave noise
        for (let y = 0; y < textureCanvas.height; y += 2) {
            for (let x = 0; x < textureCanvas.width; x += 2) {
                const variance = 8 + Math.floor(Math.random() * 20);
                tctx.fillStyle = `rgb(${126 + variance}, ${42 + Math.floor(variance * 0.4)}, ${37 + Math.floor(variance * 0.3)})`;
                tctx.fillRect(x, y, 2, 1);
            }
        }

        // Outer border
        tctx.strokeStyle = '#e8d2a8';
        tctx.lineWidth = 34;
        tctx.strokeRect(28, 28, textureCanvas.width - 56, textureCanvas.height - 56);

        tctx.strokeStyle = '#2f5f8f';
        tctx.lineWidth = 12;
        tctx.strokeRect(56, 56, textureCanvas.width - 112, textureCanvas.height - 112);

        // Repeating corner motifs
        const cornerSize = 120;
        tctx.fillStyle = '#d9bc86';
        tctx.beginPath();
        tctx.moveTo(80, 80);
        tctx.lineTo(80 + cornerSize, 80);
        tctx.lineTo(80, 80 + cornerSize);
        tctx.closePath();
        tctx.fill();

        tctx.beginPath();
        tctx.moveTo(textureCanvas.width - 80, 80);
        tctx.lineTo(textureCanvas.width - 80 - cornerSize, 80);
        tctx.lineTo(textureCanvas.width - 80, 80 + cornerSize);
        tctx.closePath();
        tctx.fill();

        tctx.beginPath();
        tctx.moveTo(80, textureCanvas.height - 80);
        tctx.lineTo(80 + cornerSize, textureCanvas.height - 80);
        tctx.lineTo(80, textureCanvas.height - 80 - cornerSize);
        tctx.closePath();
        tctx.fill();

        tctx.beginPath();
        tctx.moveTo(textureCanvas.width - 80, textureCanvas.height - 80);
        tctx.lineTo(textureCanvas.width - 80 - cornerSize, textureCanvas.height - 80);
        tctx.lineTo(textureCanvas.width - 80, textureCanvas.height - 80 - cornerSize);
        tctx.closePath();
        tctx.fill();

        // Central medallion
        tctx.beginPath();
        tctx.ellipse(textureCanvas.width / 2, textureCanvas.height / 2, 150, 210, 0, 0, Math.PI * 2);
        tctx.fillStyle = '#c8a76f';
        tctx.fill();

        tctx.beginPath();
        tctx.ellipse(textureCanvas.width / 2, textureCanvas.height / 2, 95, 140, 0, 0, Math.PI * 2);
        tctx.fillStyle = '#2e587f';
        tctx.fill();

        tctx.beginPath();
        tctx.ellipse(textureCanvas.width / 2, textureCanvas.height / 2, 45, 65, 0, 0, Math.PI * 2);
        tctx.fillStyle = '#ead7ae';
        tctx.fill();

        const rugTexture = new THREE.CanvasTexture(textureCanvas);
        rugTexture.wrapS = THREE.ClampToEdgeWrapping;
        rugTexture.wrapT = THREE.ClampToEdgeWrapping;
        rugTexture.anisotropy = 8;

        const rugTop = new THREE.Mesh(
            new THREE.PlaneGeometry(1.8, 2.4, 8, 12),
            new THREE.MeshStandardMaterial({
                map: rugTexture,
                roughness: 0.92,
                metalness: 0.0,
                side: THREE.DoubleSide
            })
        );
        rugTop.rotation.x = -Math.PI / 2;
        rugTop.position.y = 0.013;
        rugTop.receiveShadow = true;
        group.add(rugTop);

        // Thin body gives the rug depth and catches light at edges.
        const rugBody = new THREE.Mesh(
            new THREE.BoxGeometry(1.8, 0.012, 2.4),
            new THREE.MeshStandardMaterial({
                color: 0x4f2a21,
                roughness: 0.95,
                metalness: 0.0
            })
        );
        rugBody.position.y = 0.006;
        rugBody.castShadow = true;
        rugBody.receiveShadow = true;
        group.add(rugBody);

        // Fringe at both short ends.
        const fringeMaterial = new THREE.MeshStandardMaterial({
            color: 0xe7dcc4,
            roughness: 0.98,
            metalness: 0.0,
            side: THREE.DoubleSide
        });

        const frontFringe = new THREE.Mesh(new THREE.PlaneGeometry(1.7, 0.08), fringeMaterial);
        frontFringe.rotation.x = -Math.PI / 2;
        frontFringe.position.set(0, 0.014, 1.24);
        group.add(frontFringe);

        const backFringe = new THREE.Mesh(new THREE.PlaneGeometry(1.7, 0.08), fringeMaterial);
        backFringe.rotation.x = -Math.PI / 2;
        backFringe.position.set(0, 0.014, -1.24);
        group.add(backFringe);

        return group;
    }

    createCurtain() {
        const group = new THREE.Group();

        // Curtain rod
        const rod = new THREE.Mesh(
            new THREE.CylinderGeometry(0.03, 0.03, 1.95, 24),
            new THREE.MeshStandardMaterial({ color: 0x5c4d3a, roughness: 0.45, metalness: 0.25 })
        );
        rod.rotation.z = Math.PI / 2;
        rod.position.set(0, 2.08, 0.04);
        rod.castShadow = true;
        group.add(rod);

        const finialMaterial = new THREE.MeshStandardMaterial({
            color: 0x6d5a43,
            roughness: 0.42,
            metalness: 0.28
        });
        const finialLeft = new THREE.Mesh(new THREE.SphereGeometry(0.05, 18, 14), finialMaterial);
        finialLeft.position.set(-1.0, 2.08, 0.04);
        group.add(finialLeft);

        const finialRight = new THREE.Mesh(new THREE.SphereGeometry(0.05, 18, 14), finialMaterial);
        finialRight.position.set(1.0, 2.08, 0.04);
        group.add(finialRight);

        // Fabric texture with subtle vertical weave.
        const fabricCanvas = document.createElement('canvas');
        fabricCanvas.width = 512;
        fabricCanvas.height = 1024;
        const fctx = fabricCanvas.getContext('2d');

        const grad = fctx.createLinearGradient(0, 0, 0, fabricCanvas.height);
        grad.addColorStop(0, '#dce7f5');
        grad.addColorStop(0.5, '#cddcf0');
        grad.addColorStop(1, '#c0d3eb');
        fctx.fillStyle = grad;
        fctx.fillRect(0, 0, fabricCanvas.width, fabricCanvas.height);

        for (let x = 0; x < fabricCanvas.width; x += 6) {
            const alpha = x % 12 === 0 ? 0.09 : 0.045;
            fctx.fillStyle = `rgba(255,255,255,${alpha})`;
            fctx.fillRect(x, 0, 2, fabricCanvas.height);
        }

        for (let y = 0; y < fabricCanvas.height; y += 3) {
            fctx.fillStyle = `rgba(120,145,178,${0.015 + Math.random() * 0.02})`;
            fctx.fillRect(0, y, fabricCanvas.width, 1);
        }

        const fabricTexture = new THREE.CanvasTexture(fabricCanvas);
        fabricTexture.wrapS = THREE.RepeatWrapping;
        fabricTexture.wrapT = THREE.RepeatWrapping;
        fabricTexture.repeat.set(1, 1.35);

        const fabricMaterial = new THREE.MeshStandardMaterial({
            map: fabricTexture,
            roughness: 0.9,
            metalness: 0.0,
            side: THREE.DoubleSide
        });

        const createPanel = (xOffset, openDirection) => {
            const panelGeometry = new THREE.PlaneGeometry(0.9, 2.0, 18, 20);
            const positionAttr = panelGeometry.attributes.position;

            // Sculpt folds by pushing depth in a repeating wave.
            for (let i = 0; i < positionAttr.count; i++) {
                const x = positionAttr.getX(i);
                const y = positionAttr.getY(i);
                const u = (x + 0.45) / 0.9;
                const v = (y + 1.0) / 2.0;
                const wave = Math.sin(u * Math.PI * 7.0) * 0.05;
                const drape = (1.0 - v) * 0.028;

                positionAttr.setZ(i, wave + drape);
                positionAttr.setX(i, x + openDirection * (0.08 * (u - 0.5)));
            }

            positionAttr.needsUpdate = true;
            panelGeometry.computeVertexNormals();

            const panel = new THREE.Mesh(panelGeometry, fabricMaterial);
            panel.position.set(xOffset, 1.05, 0.03);
            panel.rotation.y = openDirection * 0.22;
            panel.castShadow = true;
            panel.receiveShadow = true;
            return panel;
        };

        const leftPanel = createPanel(-0.5, -1);
        const rightPanel = createPanel(0.5, 1);
        group.add(leftPanel);
        group.add(rightPanel);

        // Tiebacks to make panels feel intentionally draped.
        const tieMaterial = new THREE.MeshStandardMaterial({ color: 0xb08c5a, roughness: 0.7, metalness: 0.05 });
        const leftTie = new THREE.Mesh(new THREE.TorusGeometry(0.075, 0.01, 10, 20), tieMaterial);
        leftTie.rotation.y = Math.PI / 2;
        leftTie.position.set(-0.7, 1.1, 0.045);
        group.add(leftTie);

        const rightTie = new THREE.Mesh(new THREE.TorusGeometry(0.075, 0.01, 10, 20), tieMaterial);
        rightTie.rotation.y = Math.PI / 2;
        rightTie.position.set(0.7, 1.1, 0.045);
        group.add(rightTie);

        // Sheer inner layer for depth behind main curtains.
        const sheer = new THREE.Mesh(
            new THREE.PlaneGeometry(1.5, 1.75, 8, 8),
            new THREE.MeshStandardMaterial({
                color: 0xf4f8ff,
                roughness: 1.0,
                metalness: 0.0,
                transparent: true,
                opacity: 0.35,
                side: THREE.DoubleSide
            })
        );
        sheer.position.set(0, 1.12, 0.0);
        group.add(sheer);
        
        return group;
    }

    createWindow() {
        const group = new THREE.Group();
        const frameMaterial = new THREE.MeshBasicMaterial({
            color: 0xf2f2ee,
            side: THREE.DoubleSide
        });

        // Outdoor view texture (2D scenic image)
        const viewCanvas = document.createElement('canvas');
        viewCanvas.width = 512;
        viewCanvas.height = 512;
        const ctx = viewCanvas.getContext('2d');

        const sky = ctx.createLinearGradient(0, 0, 0, 300);
        sky.addColorStop(0, '#7fc8ff');
        sky.addColorStop(0.45, '#9fddff');
        sky.addColorStop(1, '#d9f2ff');
        ctx.fillStyle = sky;
        ctx.fillRect(0, 0, 512, 300);

        // Clouds
        ctx.fillStyle = 'rgba(255,255,255,0.78)';
        ctx.beginPath();
        ctx.ellipse(120, 90, 55, 22, 0.2, 0, Math.PI * 2);
        ctx.ellipse(170, 82, 45, 18, -0.15, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.ellipse(360, 110, 70, 26, -0.12, 0, Math.PI * 2);
        ctx.ellipse(420, 102, 50, 20, 0.09, 0, Math.PI * 2);
        ctx.fill();

        // Sea
        const sea = ctx.createLinearGradient(0, 220, 0, 400);
        sea.addColorStop(0, '#4da4d9');
        sea.addColorStop(1, '#2f7bb3');
        ctx.fillStyle = sea;
        ctx.fillRect(0, 220, 512, 180);

        // Distant mountains
        ctx.fillStyle = '#6f8e93';
        ctx.beginPath();
        ctx.moveTo(0, 255);
        ctx.lineTo(90, 205);
        ctx.lineTo(180, 245);
        ctx.lineTo(300, 210);
        ctx.lineTo(430, 242);
        ctx.lineTo(512, 220);
        ctx.lineTo(512, 280);
        ctx.lineTo(0, 280);
        ctx.closePath();
        ctx.fill();

        // Foreground greenery
        ctx.fillStyle = '#2f6a34';
        for (let i = 0; i < 24; i++) {
            const x = i * 24 + (i % 2) * 10;
            const h = 70 + Math.sin(i) * 30;
            ctx.beginPath();
            ctx.moveTo(x, 512);
            ctx.lineTo(x + 16, 512 - h);
            ctx.lineTo(x + 30, 512);
            ctx.closePath();
            ctx.fill();
        }

        const viewTexture = new THREE.CanvasTexture(viewCanvas);
        viewTexture.colorSpace = THREE.SRGBColorSpace || viewTexture.colorSpace;
        const viewMaterial = new THREE.MeshBasicMaterial({
            map: viewTexture,
            side: THREE.FrontSide,
            transparent: false
        });

        // Single interior-facing plane: visible from inside only, hidden from outside.
        const viewFront = new THREE.Mesh(new THREE.PlaneGeometry(1.16, 1.42), viewMaterial);
        viewFront.position.set(0, 1.5, 0.0008);
        // Flip so the textured front face points toward the room after wall snapping rotations.
        viewFront.rotation.y = Math.PI;
        viewFront.name = 'windowView';
        viewFront.userData.isWindowView = true;
        viewFront.renderOrder = 1;
        group.add(viewFront);

        // 2D frame strips over the view
        const topStrip = new THREE.Mesh(new THREE.PlaneGeometry(1.28, 0.08), frameMaterial);
        topStrip.position.set(0, 2.24, 0.002);
        group.add(topStrip);

        const bottomStrip = new THREE.Mesh(new THREE.PlaneGeometry(1.28, 0.08), frameMaterial);
        bottomStrip.position.set(0, 0.76, 0.002);
        group.add(bottomStrip);

        const leftStrip = new THREE.Mesh(new THREE.PlaneGeometry(0.08, 1.48), frameMaterial);
        leftStrip.position.set(-0.6, 1.5, 0.002);
        group.add(leftStrip);

        const rightStrip = new THREE.Mesh(new THREE.PlaneGeometry(0.08, 1.48), frameMaterial);
        rightStrip.position.set(0.6, 1.5, 0.002);
        group.add(rightStrip);

        // Center cross bars (2D mullions)
        const mullionMaterial = new THREE.MeshBasicMaterial({ color: 0xe9e8e2, side: THREE.DoubleSide });
        const verticalMullion = new THREE.Mesh(new THREE.PlaneGeometry(0.03, 1.42), mullionMaterial);
        verticalMullion.position.set(0, 1.5, 0.003);
        group.add(verticalMullion);

        const horizontalMullion = new THREE.Mesh(new THREE.PlaneGeometry(1.16, 0.03), mullionMaterial);
        horizontalMullion.position.set(0, 1.5, 0.003);
        group.add(horizontalMullion);

        // Simple inner glow on glass for readability
        const glaze = new THREE.Mesh(
            new THREE.PlaneGeometry(1.12, 1.38),
            new THREE.MeshBasicMaterial({ color: 0xd9eeff, transparent: true, opacity: 0.12, side: THREE.DoubleSide })
        );
        glaze.position.set(0, 1.5, 0.004);
        group.add(glaze);

        return group;
    }

    createDoor() {
        const group = new THREE.Group();

        const frameMaterial = new THREE.MeshStandardMaterial({
            color: 0x5b3a22,
            roughness: 0.78,
            metalness: 0.02
        });
        const leafMaterial = new THREE.MeshStandardMaterial({
            color: 0x7a4e2b,
            roughness: 0.72,
            metalness: 0.02
        });

        // Frame (jamb)
        const frameW = 1.02;
        const frameH = 2.12;
        const frameD = 0.12;
        const jambT = 0.065;
        const centerY = frameH / 2;

        const frameLeft = new THREE.Mesh(new THREE.BoxGeometry(jambT, frameH, frameD), frameMaterial);
        frameLeft.position.set(-(frameW / 2) + (jambT / 2), centerY, 0);
        group.add(frameLeft);

        const frameRight = new THREE.Mesh(new THREE.BoxGeometry(jambT, frameH, frameD), frameMaterial);
        frameRight.position.set((frameW / 2) - (jambT / 2), centerY, 0);
        group.add(frameRight);

        const frameTop = new THREE.Mesh(new THREE.BoxGeometry(frameW, jambT, frameD), frameMaterial);
        frameTop.position.set(0, frameH - (jambT / 2), 0);
        group.add(frameTop);

        // Main door leaf
        const leafW = 0.86;
        const leafH = 1.98;
        const leafD = 0.065;
        const leaf = new THREE.Mesh(new THREE.BoxGeometry(leafW, leafH, leafD), leafMaterial);
        leaf.position.set(0, leafH / 2, 0);
        leaf.castShadow = true;
        leaf.receiveShadow = true;
        group.add(leaf);

        // Raised panel moldings (classic 4-panel door feel)
        const trimMaterial = new THREE.MeshStandardMaterial({ color: 0x634024, roughness: 0.7, metalness: 0.02 });
        const panelDefs = [
            { x: -0.2, y: 1.42, w: 0.28, h: 0.5 },
            { x: 0.2, y: 1.42, w: 0.28, h: 0.5 },
            { x: -0.2, y: 0.68, w: 0.28, h: 0.58 },
            { x: 0.2, y: 0.68, w: 0.28, h: 0.58 }
        ];

        panelDefs.forEach((p) => {
            const panel = new THREE.Mesh(new THREE.BoxGeometry(p.w, p.h, 0.012), trimMaterial);
            panel.position.set(p.x, p.y, 0.038);
            group.add(panel);

            const inset = new THREE.Mesh(
                new THREE.BoxGeometry(p.w * 0.82, p.h * 0.78, 0.008),
                new THREE.MeshStandardMaterial({ color: 0x704628, roughness: 0.75, metalness: 0.02 })
            );
            inset.position.set(p.x, p.y, 0.0415);
            group.add(inset);
        });

        // Lockset and lever handle
        const metal = new THREE.MeshStandardMaterial({ color: 0xc8b38a, roughness: 0.3, metalness: 0.78 });
        const lockPlate = new THREE.Mesh(new THREE.CylinderGeometry(0.024, 0.024, 0.012, 16), metal);
        lockPlate.rotation.x = Math.PI / 2;
        lockPlate.position.set(0.33, 0.98, 0.041);
        group.add(lockPlate);

        const lever = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.006, 0.11, 10), metal);
        lever.rotation.z = Math.PI / 2;
        lever.position.set(0.375, 0.98, 0.046);
        group.add(lever);

        const keyhole = new THREE.Mesh(
            new THREE.CylinderGeometry(0.009, 0.009, 0.006, 12),
            new THREE.MeshStandardMaterial({ color: 0x2a2a2a, roughness: 0.4, metalness: 0.1 })
        );
        keyhole.rotation.x = Math.PI / 2;
        keyhole.position.set(0.32, 0.88, 0.0415);
        group.add(keyhole);

        // Hinges on left side
        const hingeMaterial = new THREE.MeshStandardMaterial({ color: 0x9f8457, roughness: 0.28, metalness: 0.75 });
        [0.45, 1.02, 1.58].forEach((y) => {
            const hinge = new THREE.Mesh(new THREE.CylinderGeometry(0.01, 0.01, 0.05, 10), hingeMaterial);
            hinge.rotation.z = Math.PI / 2;
            hinge.position.set(-0.43, y, 0.02);
            group.add(hinge);
        });

        // Threshold strip
        const threshold = new THREE.Mesh(
            new THREE.BoxGeometry(frameW * 0.96, 0.02, 0.15),
            new THREE.MeshStandardMaterial({ color: 0x8f7f6b, roughness: 0.42, metalness: 0.35 })
        );
        threshold.position.set(0, 0.01, 0);
        group.add(threshold);
        
        return group;
    }

    createFountain() {
        const group = new THREE.Group();
        // Stone base (hexagonal)
        const baseGeometry = new THREE.CylinderGeometry(0.38, 0.45, 0.18, 6);
        const stoneMaterial = new THREE.MeshStandardMaterial({ color: 0x8a8a8a, roughness: 0.68, metalness: 0.12 });
        const base = new THREE.Mesh(baseGeometry, stoneMaterial);
        base.position.y = 0.09;
        base.castShadow = true;
        group.add(base);

        // Main bowl (deep, round)
        const bowlGeometry = new THREE.SphereGeometry(0.28, 32, 16, 0, Math.PI * 2, 0, Math.PI / 1.2);
        const bowl = new THREE.Mesh(bowlGeometry, stoneMaterial);
        bowl.position.y = 0.22;
        bowl.castShadow = true;
        group.add(bowl);

        // Water surface (animated, blue)
        const waterGeometry = new THREE.CircleGeometry(0.22, 32);
        const waterMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x4a90e2,
            transparent: true,
            opacity: 0.7,
            roughness: 0.18,
            metalness: 0.22,
            emissive: 0x4a90e2,
            emissiveIntensity: 0.18
        });
        const water = new THREE.Mesh(waterGeometry, waterMaterial);
        water.position.y = 0.32;
        water.rotation.x = -Math.PI / 2;
        group.add(water);

        // Fountain column (center)
        const column = new THREE.Mesh(
            new THREE.CylinderGeometry(0.06, 0.09, 0.18, 18),
            new THREE.MeshStandardMaterial({ color: 0x7a7a7a, roughness: 0.55, metalness: 0.18 })
        );
        column.position.y = 0.41;
        group.add(column);

        // Water spout (top, animated drop)
        const spout = new THREE.Mesh(
            new THREE.SphereGeometry(0.03, 16, 12),
            new THREE.MeshStandardMaterial({ color: 0x4a90e2, transparent: true, opacity: 0.85, emissive: 0x4a90e2, emissiveIntensity: 0.22 })
        );
        spout.position.y = 0.52;
        group.add(spout);

        // Water streams (curved tubes)
        for (let i = 0; i < 4; i++) {
            const angle = (i / 4) * Math.PI * 2;
            const curve = new THREE.CatmullRomCurve3([
                new THREE.Vector3(0, 0.52, 0),
                new THREE.Vector3(Math.cos(angle) * 0.08, 0.48, Math.sin(angle) * 0.08),
                new THREE.Vector3(Math.cos(angle) * 0.18, 0.36, Math.sin(angle) * 0.18)
            ]);
            const tube = new THREE.Mesh(
                new THREE.TubeGeometry(curve, 20, 0.01, 8, false),
                new THREE.MeshStandardMaterial({ color: 0x4a90e2, transparent: true, opacity: 0.65, emissive: 0x4a90e2, emissiveIntensity: 0.12 })
            );
            group.add(tube);
        }

        // Decorative pebbles around base
        for (let i = 0; i < 8; i++) {
            const pebble = new THREE.Mesh(
                new THREE.SphereGeometry(0.025 + Math.random() * 0.01, 10, 8),
                new THREE.MeshStandardMaterial({ color: 0xbababa, roughness: 0.82, metalness: 0.02 })
            );
            const angle = (i / 8) * Math.PI * 2;
            pebble.position.set(Math.cos(angle) * 0.32, 0.03, Math.sin(angle) * 0.32);
            group.add(pebble);
        }
        return group;
    }

    createCrystals() {
        const group = new THREE.Group();
        // Crystal palette
        const crystalColors = [0x8a2be2, 0x00ced1, 0xffe4e1, 0x48d1cc, 0xffd700];
        // Create 5 crystals with unique shapes
        for (let i = 0; i < 5; i++) {
            const color = crystalColors[i % crystalColors.length];
            const height = 0.22 + Math.random() * 0.08;
            const radius = 0.045 + Math.random() * 0.02;
            const geometry = new THREE.OctahedronGeometry(radius, 0);
            const material = new THREE.MeshStandardMaterial({
                color,
                transparent: true,
                opacity: 0.82,
                roughness: 0.18,
                metalness: 0.22,
                emissive: color,
                emissiveIntensity: 0.12
            });
            const crystal = new THREE.Mesh(geometry, material);
            crystal.position.set(
                Math.cos(i * 1.2) * 0.13,
                height / 2,
                Math.sin(i * 1.2) * 0.13
            );
            crystal.scale.y = height / (radius * 2);
            crystal.castShadow = true;
            group.add(crystal);
        }
        // Add a circular base
        const base = new THREE.Mesh(
            new THREE.CylinderGeometry(0.18, 0.18, 0.04, 24),
            new THREE.MeshStandardMaterial({ color: 0x6a5acd, roughness: 0.72, metalness: 0.18, transparent: true, opacity: 0.65 })
        );
        base.position.y = 0.02;
        group.add(base);
        // Scatter small gem spheres
        for (let i = 0; i < 7; i++) {
            const gem = new THREE.Mesh(
                new THREE.SphereGeometry(0.018 + Math.random() * 0.008, 10, 8),
                new THREE.MeshStandardMaterial({ color: crystalColors[i % crystalColors.length], transparent: true, opacity: 0.78, roughness: 0.22, metalness: 0.22 })
            );
            const angle = (i / 7) * Math.PI * 2;
            gem.position.set(Math.cos(angle) * 0.16, 0.03, Math.sin(angle) * 0.16);
            group.add(gem);
        }
        return group;
    }

    // Plants creators
    createBamboo() {
        const group = new THREE.Group();

        const planterWood = new THREE.MeshStandardMaterial({ color: 0x7a5332, roughness: 0.78, metalness: 0.06 });
        const grassMaterial = new THREE.MeshStandardMaterial({ color: 0x4f9b3b, roughness: 0.95, metalness: 0.0 });

        // Single round wooden pot as requested.
        const planterHeight = 0.26;
        const planterRadiusTop = 0.25;
        const planterRadiusBottom = 0.21;

        const pot = new THREE.Mesh(
            new THREE.CylinderGeometry(planterRadiusTop, planterRadiusBottom, planterHeight, 28),
            planterWood
        );
        pot.position.y = planterHeight / 2;
        pot.castShadow = true;
        pot.receiveShadow = true;
        group.add(pot);

        const turf = new THREE.Mesh(
            new THREE.CylinderGeometry(planterRadiusTop * 0.88, planterRadiusTop * 0.9, 0.02, 24),
            grassMaterial
        );
        turf.position.y = planterHeight + 0.01;
        group.add(turf);

        const stemMaterial = new THREE.MeshStandardMaterial({ color: 0x4c8d3f, roughness: 0.7, metalness: 0.02 });
        const nodeMaterial = new THREE.MeshStandardMaterial({ color: 0x6ea950, roughness: 0.68, metalness: 0.02 });
        const leafMaterial = new THREE.MeshStandardMaterial({
            color: 0x86b867,
            roughness: 0.84,
            metalness: 0.0,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.95
        });

        const makeLeaf = (length, width) => {
            const geom = new THREE.PlaneGeometry(length, width, 8, 1);
            const pos = geom.attributes.position;
            for (let i = 0; i < pos.count; i++) {
                const x = pos.getX(i);
                const t = (x + length * 0.5) / length;
                pos.setZ(i, Math.sin(t * Math.PI) * 0.012);
            }
            pos.needsUpdate = true;
            geom.computeVertexNormals();
            return new THREE.Mesh(geom, leafMaterial);
        };

        const caneCount = 16;
        const baseY = planterHeight + 0.015;

        // Dense slim canes distributed inside one round pot.
        for (let i = 0; i < caneCount; i++) {
            const ring = i % 3;
            const angle = (i / caneCount) * Math.PI * 2 + (ring * 0.22);
            const radiusFactor = ring === 0 ? 0.18 : (ring === 1 ? 0.42 : 0.65);
            const radiusSpread = planterRadiusTop * radiusFactor;
            const x = Math.cos(angle) * radiusSpread;
            const z = Math.sin(angle) * radiusSpread * 0.72;
            const height = 1.2 + (i % 5) * 0.14;
            const radius = 0.008 + (i % 3) * 0.0014;

            const cane = new THREE.Group();
            const segmentCount = Math.max(6, Math.floor(height / 0.22));
            const segH = height / segmentCount;

            for (let s = 0; s < segmentCount; s++) {
                const segment = new THREE.Mesh(
                    new THREE.CylinderGeometry(radius * 0.98, radius, segH * 0.95, 10),
                    stemMaterial
                );
                segment.position.y = baseY + segH * (s + 0.5);
                segment.castShadow = true;
                cane.add(segment);

                if (s < segmentCount - 1) {
                    const node = new THREE.Mesh(
                        new THREE.TorusGeometry(radius * 1.03, radius * 0.18, 7, 16),
                        nodeMaterial
                    );
                    node.rotation.x = Math.PI / 2;
                    node.position.y = baseY + segH * (s + 1);
                    cane.add(node);
                }
            }

            cane.position.set(x, 0, z);
            cane.rotation.x = (Math.sin(i * 1.7) * 0.018);
            cane.rotation.z = (Math.cos(i * 1.3) * 0.024);
            group.add(cane);

            // Leaf clusters distributed along upper 70% of each cane.
            const leafStart = baseY + height * 0.32;
            const leafSets = 5 + (i % 3);
            for (let l = 0; l < leafSets; l++) {
                const y = leafStart + l * (height * 0.55 / leafSets);
                const spin = (i * 0.7 + l * 0.95);
                const len = 0.12 + ((l + i) % 4) * 0.015;

                const leafA = makeLeaf(len, 0.024);
                leafA.position.set(x + 0.012, y, z + 0.005);
                leafA.rotation.set(-0.3, spin, 0.08);
                leafA.castShadow = true;
                group.add(leafA);

                const leafB = makeLeaf(len * 0.9, 0.022);
                leafB.position.set(x - 0.012, y + 0.015, z - 0.005);
                leafB.rotation.set(-0.38, spin + Math.PI * 0.65, -0.08);
                leafB.castShadow = true;
                group.add(leafB);
            }
        }
        
        return group;
    }

    createPlant() {
        const group = new THREE.Group();
        
        // Modern ceramic pot
        const potGeometry = new THREE.CylinderGeometry(0.15, 0.12, 0.25, 16);
        const potMaterial = new THREE.MeshStandardMaterial({ 
            color: 0xe8e8e8,
            roughness: 0.6,
            metalness: 0.2
        });
        const pot = new THREE.Mesh(potGeometry, potMaterial);
        pot.position.y = 0.125;
        pot.castShadow = true;
        group.add(pot);
        
        // Soil
        const soilGeometry = new THREE.CylinderGeometry(0.14, 0.14, 0.05, 16);
        const soilMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x3d2817,
            roughness: 0.9
        });
        const soil = new THREE.Mesh(soilGeometry, soilMaterial);
        soil.position.y = 0.27;
        group.add(soil);
        
        // Plant stems and leaves (more realistic)
        const leafMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x2d5016,
            side: THREE.DoubleSide,
            roughness: 0.8
        });
        
        // Create multiple stems with leaves
        for (let i = 0; i < 5; i++) {
            // Stem
            const stemGeometry = new THREE.CylinderGeometry(0.01, 0.015, 0.4, 8);
            const stemMaterial = new THREE.MeshStandardMaterial({ 
                color: 0x355e3b,
                roughness: 0.7
            });
            const stem = new THREE.Mesh(stemGeometry, stemMaterial);
            const angle = (i / 5) * Math.PI * 2;
            stem.position.set(
                Math.cos(angle) * 0.05,
                0.45,
                Math.sin(angle) * 0.05
            );
            stem.rotation.z = Math.cos(angle) * 0.2;
            stem.rotation.x = Math.sin(angle) * 0.2;
            stem.castShadow = true;
            group.add(stem);
            
            // Leaves on stem
            for (let j = 0; j < 3; j++) {
                const leafGeometry = new THREE.CircleGeometry(0.08, 8);
                const leaf = new THREE.Mesh(leafGeometry, leafMaterial);
                leaf.position.set(
                    Math.cos(angle) * 0.05 + Math.cos(angle + j) * 0.08,
                    0.35 + (j * 0.12),
                    Math.sin(angle) * 0.05 + Math.sin(angle + j) * 0.08
                );
                leaf.rotation.y = angle + (j * 0.5);
                leaf.rotation.x = 0.3;
                leaf.castShadow = true;
                group.add(leaf);
            }
        }
        
        return group;
    }

    createBonsai() {
        const group = new THREE.Group();

        // Shallow ceramic bonsai pot
        const potProfile = [
            new THREE.Vector2(0.17, 0.0),
            new THREE.Vector2(0.2, 0.02),
            new THREE.Vector2(0.21, 0.08),
            new THREE.Vector2(0.19, 0.14),
            new THREE.Vector2(0.16, 0.16),
            new THREE.Vector2(0.14, 0.17)
        ];
        const pot = new THREE.Mesh(
            new THREE.LatheGeometry(potProfile, 36),
            new THREE.MeshStandardMaterial({ color: 0x706d66, roughness: 0.65, metalness: 0.08 })
        );
        pot.position.y = 0.01;
        pot.castShadow = true;
        pot.receiveShadow = true;
        group.add(pot);

        const soil = new THREE.Mesh(
            new THREE.CylinderGeometry(0.155, 0.155, 0.04, 24),
            new THREE.MeshStandardMaterial({ color: 0x3e2b1e, roughness: 0.96, metalness: 0.0 })
        );
        soil.position.y = 0.16;
        group.add(soil);

        const trunkMaterial = new THREE.MeshStandardMaterial({ color: 0x6a4328, roughness: 0.9, metalness: 0.0 });

        // Curved bonsai trunk
        const trunkCurve = new THREE.CatmullRomCurve3([
            new THREE.Vector3(0, 0.14, 0),
            new THREE.Vector3(0.02, 0.24, 0.01),
            new THREE.Vector3(0.06, 0.34, -0.02),
            new THREE.Vector3(0.03, 0.46, -0.06),
            new THREE.Vector3(-0.02, 0.58, -0.08)
        ]);
        const trunk = new THREE.Mesh(new THREE.TubeGeometry(trunkCurve, 30, 0.03, 12, false), trunkMaterial);
        trunk.castShadow = true;
        trunk.receiveShadow = true;
        group.add(trunk);

        const branchMaterial = new THREE.MeshStandardMaterial({ color: 0x5d3b24, roughness: 0.88, metalness: 0.0 });
        const branchDefs = [
            { pos: [0.03, 0.36, -0.03], rotZ: -0.85, rotY: 0.35, len: 0.22, rTop: 0.009, rBottom: 0.013 },
            { pos: [0.00, 0.43, -0.06], rotZ: 0.7, rotY: -0.4, len: 0.2, rTop: 0.008, rBottom: 0.012 },
            { pos: [-0.01, 0.51, -0.08], rotZ: -0.35, rotY: 0.9, len: 0.16, rTop: 0.007, rBottom: 0.01 }
        ];

        branchDefs.forEach((b) => {
            const branch = new THREE.Mesh(
                new THREE.CylinderGeometry(b.rTop, b.rBottom, b.len, 10),
                branchMaterial
            );
            branch.position.set(b.pos[0], b.pos[1], b.pos[2]);
            branch.rotation.z = b.rotZ;
            branch.rotation.y = b.rotY;
            branch.castShadow = true;
            group.add(branch);
        });

        // Exposed roots at soil line
        const rootDefs = [
            { x: -0.03, z: 0.015, ry: 0.8 },
            { x: 0.025, z: -0.01, ry: -0.55 },
            { x: 0.008, z: 0.03, ry: 1.7 }
        ];
        rootDefs.forEach((r) => {
            const root = new THREE.Mesh(new THREE.CylinderGeometry(0.004, 0.007, 0.08, 8), branchMaterial);
            root.position.set(r.x, 0.165, r.z);
            root.rotation.z = 1.2;
            root.rotation.y = r.ry;
            root.castShadow = true;
            group.add(root);
        });

        const foliageMaterial = new THREE.MeshStandardMaterial({ color: 0x2f6f2d, roughness: 0.82, metalness: 0.0 });
        const padDefs = [
            { x: 0.15, y: 0.39, z: -0.06, sx: 1.2, sy: 0.55, sz: 1.0 },
            { x: -0.14, y: 0.46, z: -0.08, sx: 1.15, sy: 0.58, sz: 1.0 },
            { x: 0.02, y: 0.61, z: -0.1, sx: 1.25, sy: 0.52, sz: 1.05 },
            { x: -0.03, y: 0.35, z: 0.02, sx: 0.95, sy: 0.5, sz: 0.9 }
        ];

        // Flattened foliage pads are a key bonsai visual cue.
        padDefs.forEach((p) => {
            const pad = new THREE.Mesh(new THREE.SphereGeometry(0.11, 16, 14), foliageMaterial);
            pad.position.set(p.x, p.y, p.z);
            pad.scale.set(p.sx, p.sy, p.sz);
            pad.castShadow = true;
            group.add(pad);
        });

        // Subtle lighter tips for depth
        const tipMaterial = new THREE.MeshStandardMaterial({ color: 0x4f8f45, roughness: 0.8, metalness: 0.0 });
        padDefs.forEach((p, idx) => {
            const tip = new THREE.Mesh(new THREE.SphereGeometry(0.045, 12, 10), tipMaterial);
            tip.position.set(p.x + (idx % 2 ? -0.02 : 0.02), p.y + 0.035, p.z + 0.015);
            tip.castShadow = true;
            group.add(tip);
        });
        
        return group;
    }

    createFlowers() {
        const group = new THREE.Group();

        const pot = new THREE.Mesh(
            new THREE.CylinderGeometry(0.13, 0.1, 0.2, 20),
            new THREE.MeshStandardMaterial({ color: 0xc97c5d, roughness: 0.78, metalness: 0.04 })
        );
        pot.position.y = 0.1;
        pot.castShadow = true;
        pot.receiveShadow = true;
        group.add(pot);

        const rim = new THREE.Mesh(
            new THREE.TorusGeometry(0.128, 0.008, 10, 24),
            new THREE.MeshStandardMaterial({ color: 0xb56f54, roughness: 0.72, metalness: 0.04 })
        );
        rim.rotation.x = Math.PI / 2;
        rim.position.y = 0.2;
        group.add(rim);

        const soil = new THREE.Mesh(
            new THREE.CylinderGeometry(0.108, 0.108, 0.04, 18),
            new THREE.MeshStandardMaterial({ color: 0x3e2a1f, roughness: 0.95, metalness: 0.0 })
        );
        soil.position.y = 0.205;
        group.add(soil);

        const stemMaterial = new THREE.MeshStandardMaterial({ color: 0x3f7f38, roughness: 0.86, metalness: 0.0 });
        const leafMaterial = new THREE.MeshStandardMaterial({
            color: 0x4e8c43,
            roughness: 0.82,
            metalness: 0.0,
            side: THREE.DoubleSide
        });

        const flowerPalette = [0xf06f98, 0xffb84d, 0xe95f5f, 0xd78cff, 0xffe37b];

        const makeFlowerHead = (color) => {
            const flowerGroup = new THREE.Group();
            const petalMaterial = new THREE.MeshStandardMaterial({
                color,
                roughness: 0.72,
                metalness: 0.0,
                side: THREE.DoubleSide
            });

            for (let p = 0; p < 8; p++) {
                const petal = new THREE.Mesh(new THREE.CircleGeometry(0.028, 14), petalMaterial);
                const angle = (p / 8) * Math.PI * 2;
                petal.position.set(Math.cos(angle) * 0.03, Math.sin(angle) * 0.03, 0);
                petal.rotation.x = -0.2;
                petal.rotation.y = angle;
                petal.castShadow = true;
                flowerGroup.add(petal);
            }

            const center = new THREE.Mesh(
                new THREE.SphereGeometry(0.015, 12, 10),
                new THREE.MeshStandardMaterial({ color: 0xf1cf4f, roughness: 0.75, metalness: 0.0 })
            );
            center.castShadow = true;
            flowerGroup.add(center);

            return flowerGroup;
        };

        const stemDefs = [
            { x: -0.055, z: 0.01, h: 0.34, bendX: 0.18, bendZ: -0.1 },
            { x: -0.02, z: -0.04, h: 0.31, bendX: 0.12, bendZ: 0.08 },
            { x: 0.02, z: 0.045, h: 0.36, bendX: -0.16, bendZ: 0.06 },
            { x: 0.055, z: -0.02, h: 0.33, bendX: -0.12, bendZ: -0.09 },
            { x: 0.0, z: 0.0, h: 0.38, bendX: 0.08, bendZ: 0.0 }
        ];

        stemDefs.forEach((s, i) => {
            const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.005, 0.007, s.h, 8), stemMaterial);
            stem.position.set(s.x, 0.22 + s.h / 2, s.z);
            stem.rotation.x = s.bendX;
            stem.rotation.z = s.bendZ;
            stem.castShadow = true;
            group.add(stem);

            for (let l = 0; l < 2; l++) {
                const leaf = new THREE.Mesh(new THREE.PlaneGeometry(0.07, 0.035), leafMaterial);
                const dir = l === 0 ? 1 : -1;
                leaf.position.set(
                    s.x + dir * 0.022,
                    0.25 + (l * 0.07) + (i % 2) * 0.03,
                    s.z + dir * 0.01
                );
                leaf.rotation.set(-0.4, dir * 0.8, dir * 0.15);
                leaf.castShadow = true;
                group.add(leaf);
            }

            const bloom = makeFlowerHead(flowerPalette[i % flowerPalette.length]);
            bloom.position.set(s.x + s.bendZ * 0.03, 0.22 + s.h + 0.005, s.z - s.bendX * 0.02);
            bloom.rotation.x = -0.22;
            bloom.rotation.y = i * 0.6;
            group.add(bloom);
        });
        
        return group;
    }

    // Lighting creators
    createLamp() {
        const group = new THREE.Group();

        const metalMaterial = new THREE.MeshStandardMaterial({
            color: 0xb7bcc6,
            roughness: 0.28,
            metalness: 0.82
        });

        // Weighted round base
        const base = new THREE.Mesh(
            new THREE.CylinderGeometry(0.19, 0.21, 0.05, 28),
            metalMaterial
        );
        base.position.y = 0.025;
        base.castShadow = true;
        base.receiveShadow = true;
        group.add(base);

        const pole = new THREE.Mesh(
            new THREE.CylinderGeometry(0.018, 0.02, 1.0, 14),
            metalMaterial
        );
        pole.position.y = 0.54;
        pole.castShadow = true;
        group.add(pole);

        const collar = new THREE.Mesh(
            new THREE.TorusGeometry(0.024, 0.004, 10, 20),
            new THREE.MeshStandardMaterial({ color: 0x51545a, roughness: 0.32, metalness: 0.78 })
        );
        collar.rotation.x = Math.PI / 2;
        collar.position.y = 1.06;
        group.add(collar);

        // Clear cone shade with visible top and bottom rims.
        const shade = new THREE.Mesh(
            new THREE.CylinderGeometry(0.13, 0.24, 0.28, 30, 1, true),
            new THREE.MeshStandardMaterial({
                color: 0xc7b69a,
                roughness: 0.92,
                metalness: 0.0,
                side: THREE.DoubleSide
            })
        );
        shade.position.y = 1.17;
        shade.castShadow = true;
        group.add(shade);

        const rimMaterial = new THREE.MeshStandardMaterial({ color: 0xc5a56b, roughness: 0.35, metalness: 0.65 });
        const topRim = new THREE.Mesh(new THREE.TorusGeometry(0.13, 0.006, 10, 24), rimMaterial);
        topRim.rotation.x = Math.PI / 2;
        topRim.position.y = 1.30;
        group.add(topRim);

        const bottomRim = new THREE.Mesh(new THREE.TorusGeometry(0.24, 0.006, 10, 28), rimMaterial);
        bottomRim.rotation.x = Math.PI / 2;
        bottomRim.position.y = 1.03;
        group.add(bottomRim);

        // Off-state bulb and top cap: visible shape without light emission.
        const bulb = new THREE.Mesh(
            new THREE.SphereGeometry(0.07, 18, 16),
            new THREE.MeshStandardMaterial({
                color: 0xe6e6df,
                roughness: 0.72,
                metalness: 0.0
            })
        );
        bulb.position.y = 1.15;
        group.add(bulb);

        const topCap = new THREE.Mesh(
            new THREE.CircleGeometry(0.13, 24),
            new THREE.MeshStandardMaterial({ color: 0xb29b74, roughness: 0.38, metalness: 0.62, side: THREE.DoubleSide })
        );
        topCap.rotation.x = Math.PI / 2;
        topCap.position.y = 1.301;
        group.add(topCap);

        // Pull chain detail
        const chain = new THREE.Mesh(
            new THREE.CylinderGeometry(0.003, 0.003, 0.17, 8),
            new THREE.MeshStandardMaterial({ color: 0xb9a57c, roughness: 0.35, metalness: 0.7 })
        );
        chain.position.set(0.09, 1.12, 0.02);
        group.add(chain);

        const chainTip = new THREE.Mesh(
            new THREE.SphereGeometry(0.01, 10, 10),
            new THREE.MeshStandardMaterial({ color: 0xc9b690, roughness: 0.3, metalness: 0.72 })
        );
        chainTip.position.set(0.09, 1.035, 0.02);
        group.add(chainTip);
        
        return group;
    }

    createChandelier() {
        const group = new THREE.Group();

        const brassMaterial = new THREE.MeshStandardMaterial({
            color: 0xc7a45d,
            metalness: 0.82,
            roughness: 0.28
        });

        // Ceiling canopy and chain
        const canopy = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.1, 0.04, 20), brassMaterial);
        canopy.position.y = 2.38;
        canopy.castShadow = true;
        group.add(canopy);

        const chain = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.38, 10), brassMaterial);
        chain.position.y = 2.17;
        group.add(chain);

        // Center hub and main ring
        const hub = new THREE.Mesh(new THREE.SphereGeometry(0.065, 16, 14), brassMaterial);
        hub.position.y = 1.95;
        hub.castShadow = true;
        group.add(hub);

        const ring = new THREE.Mesh(new THREE.TorusGeometry(0.36, 0.018, 12, 40), brassMaterial);
        ring.rotation.x = Math.PI / 2;
        ring.position.y = 1.85;
        ring.castShadow = true;
        group.add(ring);

        // Curved support arms + candle cups + bulbs
        const armCount = 6;
        for (let i = 0; i < armCount; i++) {
            const angle = (i / armCount) * Math.PI * 2;

            const arm = new THREE.Mesh(
                new THREE.CylinderGeometry(0.012, 0.014, 0.34, 10),
                brassMaterial
            );
            arm.position.set(Math.cos(angle) * 0.18, 1.86, Math.sin(angle) * 0.18);
            arm.rotation.z = Math.PI / 2.4;
            arm.rotation.y = angle;
            arm.castShadow = true;
            group.add(arm);

            const cup = new THREE.Mesh(
                new THREE.CylinderGeometry(0.035, 0.025, 0.05, 14),
                new THREE.MeshStandardMaterial({ color: 0xd9c39c, metalness: 0.7, roughness: 0.35 })
            );
            cup.position.set(Math.cos(angle) * 0.39, 1.75, Math.sin(angle) * 0.39);
            cup.castShadow = true;
            group.add(cup);

            const bulb = new THREE.Mesh(
                new THREE.SphereGeometry(0.03, 14, 12),
                new THREE.MeshStandardMaterial({
                    color: 0xfff0cf,
                    emissive: 0xffd79a,
                    emissiveIntensity: 0.65,
                    transparent: true,
                    opacity: 0.95
                })
            );
            bulb.position.set(Math.cos(angle) * 0.39, 1.79, Math.sin(angle) * 0.39);
            group.add(bulb);

            // Crystal drop under each cup
            const drop = new THREE.Mesh(
                new THREE.OctahedronGeometry(0.022, 0),
                new THREE.MeshStandardMaterial({
                    color: 0xd7efff,
                    transparent: true,
                    opacity: 0.72,
                    roughness: 0.05,
                    metalness: 0.0
                })
            );
            drop.position.set(Math.cos(angle) * 0.39, 1.69, Math.sin(angle) * 0.39);
            group.add(drop);
        }

        // Bottom finial
        const finial = new THREE.Mesh(
            new THREE.ConeGeometry(0.03, 0.08, 14),
            new THREE.MeshStandardMaterial({ color: 0xc2a062, metalness: 0.78, roughness: 0.3 })
        );
        finial.position.y = 1.72;
        group.add(finial);

        // Invisible hit proxy so selecting/editing with mouse is easier.
        const hitProxy = new THREE.Mesh(
            new THREE.CylinderGeometry(0.45, 0.45, 0.9, 14),
            new THREE.MeshBasicMaterial({
                color: 0xffffff,
                transparent: true,
                opacity: 0.01,
                depthWrite: false,
                side: THREE.DoubleSide
            })
        );
        hitProxy.position.y = 1.95;
        hitProxy.userData.isSelectionProxy = true;
        group.add(hitProxy);
        
        return group;
    }

    createCandle() {
        const group = new THREE.Group();
        
        // Candle body
        const bodyGeometry = new THREE.CylinderGeometry(0.04, 0.04, 0.2, 16);
        const bodyMaterial = new THREE.MeshStandardMaterial({ color: 0xfffacd });
        const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
        body.position.y = 0.1;
        group.add(body);
        
        // Flame
        const flameGeometry = new THREE.SphereGeometry(0.03, 8, 8);
        const flameMaterial = new THREE.MeshStandardMaterial({ 
            color: 0xffa500,
            emissive: 0xffa500,
            emissiveIntensity: 0.8
        });
        const flame = new THREE.Mesh(flameGeometry, flameMaterial);
        flame.position.y = 0.23;
        group.add(flame);
        
        return group;
    }

    createDefaultBox(type) {
        const geometry = new THREE.BoxGeometry(0.5, 0.5, 0.5);
        const material = new THREE.MeshStandardMaterial({ color: 0x888888 });
        const box = new THREE.Mesh(geometry, material);
        box.position.y = 0.25;
        
        const group = new THREE.Group();
        group.add(box);
        return group;
    }
}

// Export to global scope
window.ObjectLoader = ObjectLoader;
