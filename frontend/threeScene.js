/**
 * Three.js Scene Manager for Feng Shui Room Designer
 * Handles scene initialization, camera controls, lighting, and room construction
 */

class ThreeScene {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`Container ${containerId} not found`);
        }

        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.room = null;
        this.objects = [];
        
        // Store wall references for dynamic transparency
        this.walls = {
            north: null,  // back wall (negative Z)
            south: null,  // front wall (positive Z)
            east: null,   // right wall (positive X)
            west: null    // left wall (negative X)
        };
        
        this.init();
    }

    init() {
        // Create scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0xf5f5f5);

        // Setup camera
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
        this.camera.position.set(0, 5, 8);
        this.camera.lookAt(0, 0, 0);

        // Create renderer
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true,
            alpha: true 
        });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        
        // Clear container and add canvas
        this.container.innerHTML = '';
        this.container.appendChild(this.renderer.domElement);

        // Setup orbit controls for 360° rotation
        if (typeof THREE.OrbitControls === 'undefined') {
            throw new Error('OrbitControls not loaded. Please check internet connection.');
        }
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.minDistance = 3;
        this.controls.maxDistance = 20;
        this.controls.maxPolarAngle = Math.PI / 2.1; // Prevent camera going below floor
        this.controls.target.set(0, 0, 0);

        // Add lighting
        this.setupLighting();

        // Create the room
        this.createRoom();

        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize());

        // Start animation loop
        this.animate();
    }

    setupLighting() {
        // Warm ambient light for cozy bedroom atmosphere
        const ambientLight = new THREE.AmbientLight(0xfff4e6, 0.6);
        this.scene.add(ambientLight);

        // Main directional light (natural sunlight from window)
        const directionalLight = new THREE.DirectionalLight(0xfff8dc, 1.0);
        directionalLight.position.set(8, 10, 6);
        directionalLight.castShadow = true;
        directionalLight.shadow.camera.left = -10;
        directionalLight.shadow.camera.right = 10;
        directionalLight.shadow.camera.top = 10;
        directionalLight.shadow.camera.bottom = -10;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.bias = -0.0005;
        this.scene.add(directionalLight);

        // Soft fill light from opposite side
        const fillLight = new THREE.PointLight(0xffe4b5, 0.4);
        fillLight.position.set(-5, 4, -5);
        this.scene.add(fillLight);
        
        // Ceiling spot light for modern look
        const spotLight = new THREE.SpotLight(0xffffff, 0.5);
        spotLight.position.set(0, 2.8, 0);
        spotLight.angle = Math.PI / 4;
        spotLight.penumbra = 0.3;
        spotLight.castShadow = true;
        this.scene.add(spotLight);

        // Hemisphere light for natural ambient
        const hemisphereLight = new THREE.HemisphereLight(0xffffff, 0xb8a890, 0.4);
        this.scene.add(hemisphereLight);
            // Area light for soft shadow and realism
            if (THREE.RectAreaLight) {
                const areaLight = new THREE.RectAreaLight(0xffffff, 1.2, 3, 1.2);
                areaLight.position.set(0, 2.7, 0);
                areaLight.lookAt(0, 0, 0);
                this.scene.add(areaLight);
            }
    }

    createRoom() {
        const roomGroup = new THREE.Group();
        
        // Room dimensions (6m x 6m x 3m ceiling height)
        const roomWidth = 6;
        const roomDepth = 6;
        const roomHeight = 3;
        
        // Store room dimensions for boundary checking
        this.roomDimensions = {
            width: roomWidth,
            depth: roomDepth,
            height: roomHeight
        };

        // Floor with realistic glossy marble tile texture
        const floorGeometry = new THREE.PlaneGeometry(roomWidth, roomDepth);
        
        // Create high-quality procedural marble tile texture
        const floorCanvas = document.createElement('canvas');
        floorCanvas.width = 1024;
        floorCanvas.height = 1024;
        const floorCtx = floorCanvas.getContext('2d');
        
        // Tile dimensions
        const tileSize = 256; // 4x4 tiles in 1024x1024 canvas
        const groutWidth = 3;
        
        // Base marble colors - light beige/cream palette
        const marbleBaseColors = [
            '#f5f3ef', '#f0ebe5', '#ede9e3', '#f2ede7', '#f7f4f0',
            '#f3efe9', '#f1ede8', '#f4f0ea', '#f6f2ec', '#f0ece6'
        ];
        
        // Draw tiles
        for (let row = 0; row < 4; row++) {
            for (let col = 0; col < 4; col++) {
                const x = col * tileSize;
                const y = row * tileSize;
                
                // Select random base color for this tile
                const baseColor = marbleBaseColors[Math.floor(Math.random() * marbleBaseColors.length)];
                
                // Fill tile base
                floorCtx.fillStyle = baseColor;
                floorCtx.fillRect(x, y, tileSize - groutWidth, tileSize - groutWidth);
                
                // Add subtle color variations
                for (let i = 0; i < 15; i++) {
                    const varX = x + Math.random() * (tileSize - groutWidth);
                    const varY = y + Math.random() * (tileSize - groutWidth);
                    const varSize = 20 + Math.random() * 40;
                    const opacity = 0.02 + Math.random() * 0.04;
                    
                    const gradient = floorCtx.createRadialGradient(varX, varY, 0, varX, varY, varSize);
                    gradient.addColorStop(0, `rgba(220, 210, 200, ${opacity})`);
                    gradient.addColorStop(1, 'rgba(220, 210, 200, 0)');
                    floorCtx.fillStyle = gradient;
                    floorCtx.fillRect(x, y, tileSize - groutWidth, tileSize - groutWidth);
                }
                
                // Add marble veining
                const numVeins = 3 + Math.floor(Math.random() * 4);
                for (let v = 0; v < numVeins; v++) {
                    floorCtx.strokeStyle = `rgba(200, 190, 180, ${0.15 + Math.random() * 0.2})`;
                    floorCtx.lineWidth = 0.5 + Math.random() * 1.5;
                    floorCtx.beginPath();
                    
                    const startX = x + Math.random() * (tileSize - groutWidth);
                    const startY = y + Math.random() * (tileSize - groutWidth);
                    floorCtx.moveTo(startX, startY);
                    
                    // Create wavy vein pattern
                    const points = 8 + Math.floor(Math.random() * 6);
                    for (let p = 0; p < points; p++) {
                        const veinX = startX + (Math.random() - 0.5) * (tileSize * 0.6);
                        const veinY = startY + (Math.random() - 0.5) * (tileSize * 0.6);
                        floorCtx.lineTo(veinX, veinY);
                    }
                    floorCtx.stroke();
                }
                
                // Add subtle highlights for glossy effect
                for (let h = 0; h < 8; h++) {
                    const hX = x + Math.random() * (tileSize - groutWidth);
                    const hY = y + Math.random() * (tileSize - groutWidth);
                    const hSize = 5 + Math.random() * 15;
                    
                    const highlightGrad = floorCtx.createRadialGradient(hX, hY, 0, hX, hY, hSize);
                    highlightGrad.addColorStop(0, 'rgba(255, 255, 255, 0.08)');
                    highlightGrad.addColorStop(1, 'rgba(255, 255, 255, 0)');
                    floorCtx.fillStyle = highlightGrad;
                    floorCtx.fillRect(x, y, tileSize - groutWidth, tileSize - groutWidth);
                }
            }
        }
        
        // Add grout lines
        floorCtx.fillStyle = '#d0cac4'; // Light grout color
        // Vertical grout lines
        for (let col = 0; col <= 4; col++) {
            const x = col * tileSize - groutWidth;
            floorCtx.fillRect(x, 0, groutWidth, 1024);
        }
        // Horizontal grout lines
        for (let row = 0; row <= 4; row++) {
            const y = row * tileSize - groutWidth;
            floorCtx.fillRect(0, y, 1024, groutWidth);
        }
        
        // Add subtle shadow to grout for depth
        floorCtx.strokeStyle = 'rgba(0, 0, 0, 0.1)';
        floorCtx.lineWidth = 1;
        for (let col = 0; col <= 4; col++) {
            const x = col * tileSize;
            floorCtx.beginPath();
            floorCtx.moveTo(x, 0);
            floorCtx.lineTo(x, 1024);
            floorCtx.stroke();
        }
        for (let row = 0; row <= 4; row++) {
            const y = row * tileSize;
            floorCtx.beginPath();
            floorCtx.moveTo(0, y);
            floorCtx.lineTo(1024, y);
            floorCtx.stroke();
        }
        
        const floorTexture = new THREE.CanvasTexture(floorCanvas);
        floorTexture.wrapS = THREE.RepeatWrapping;
        floorTexture.wrapT = THREE.RepeatWrapping;
        floorTexture.repeat.set(2, 2);
        
        const floorMaterial = new THREE.MeshStandardMaterial({ 
            map: floorTexture,
            roughness: 0.15,  // Very low for glossy/glassy effect
            metalness: 0.25,  // Some metalness for reflection
            envMapIntensity: 1.2  // Enhanced reflections
        });
        const floor = new THREE.Mesh(floorGeometry, floorMaterial);
        floor.rotation.x = -Math.PI / 2;
        floor.position.y = 0;
        floor.receiveShadow = true;
        floor.userData.isFloor = true;
        roomGroup.add(floor);
        this.floor = floor;

        // Wall geometry
        const wallGeometry = new THREE.PlaneGeometry(roomWidth, roomHeight);
        
        // Create wall material with realistic paint texture
        const createWallMaterial = () => {
            // Create high-quality paint texture
            const wallCanvas = document.createElement('canvas');
            wallCanvas.width = 1024;
            wallCanvas.height = 1024;
            const wallCtx = wallCanvas.getContext('2d');
            
            // Base paint color - warm off-white
            const baseColor = '#f0ebe5';
            wallCtx.fillStyle = baseColor;
            wallCtx.fillRect(0, 0, 1024, 1024);
            
            // Add subtle paint roller texture
            for (let i = 0; i < 1000; i++) {
                const x = Math.random() * 1024;
                const y = Math.random() * 1024;
                const size = Math.random() * 3 + 1;
                const opacity = Math.random() * 0.015 + 0.005;
                
                wallCtx.fillStyle = Math.random() > 0.5 ? 
                    `rgba(220, 210, 200, ${opacity})` : 
                    `rgba(180, 170, 160, ${opacity})`;
                wallCtx.fillRect(x, y, size, size);
            }
            
            // Add very subtle vertical brush strokes
            wallCtx.globalAlpha = 0.02;
            for (let x = 0; x < 1024; x += 8) {
                const offset = Math.random() * 4 - 2;
                wallCtx.strokeStyle = Math.random() > 0.5 ? '#e8e3dd' : '#d8d3cd';
                wallCtx.lineWidth = 2 + Math.random() * 2;
                wallCtx.beginPath();
                wallCtx.moveTo(x + offset, 0);
                wallCtx.lineTo(x + offset, 1024);
                wallCtx.stroke();
            }
            wallCtx.globalAlpha = 1.0;
            
            // Add slight imperfections
            for (let i = 0; i < 50; i++) {
                const x = Math.random() * 1024;
                const y = Math.random() * 1024;
                const radius = Math.random() * 2 + 1;
                const opacity = Math.random() * 0.02;
                
                wallCtx.fillStyle = `rgba(160, 150, 140, ${opacity})`;
                wallCtx.beginPath();
                wallCtx.arc(x, y, radius, 0, Math.PI * 2);
                wallCtx.fill();
            }
            
            const wallTexture = new THREE.CanvasTexture(wallCanvas);
            wallTexture.wrapS = THREE.RepeatWrapping;
            wallTexture.wrapT = THREE.RepeatWrapping;
            wallTexture.repeat.set(2, 2);
            
            return new THREE.MeshStandardMaterial({
                map: wallTexture,
                color: 0xffffff,
                side: THREE.DoubleSide,
                transparent: true,
                opacity: 1.0,
                roughness: 0.92,
                metalness: 0.0,
                envMapIntensity: 0.3
            });
        };

        // North wall (back) - negative Z
        const northWall = new THREE.Mesh(wallGeometry, createWallMaterial());
        northWall.position.set(0, roomHeight / 2, -roomDepth / 2);
        northWall.receiveShadow = true;
        northWall.userData.wallSide = 'north';
        roomGroup.add(northWall);
        this.walls.north = northWall;

        // South wall (front) - positive Z
        const southWall = new THREE.Mesh(wallGeometry, createWallMaterial());
        southWall.position.set(0, roomHeight / 2, roomDepth / 2);
        southWall.rotation.y = Math.PI;
        southWall.receiveShadow = true;
        southWall.userData.wallSide = 'south';
        roomGroup.add(southWall);
        this.walls.south = southWall;

        // West wall (left) - negative X
        const westWall = new THREE.Mesh(wallGeometry, createWallMaterial());
        westWall.position.set(-roomWidth / 2, roomHeight / 2, 0);
        westWall.rotation.y = Math.PI / 2;
        westWall.receiveShadow = true;
        westWall.userData.wallSide = 'west';
        roomGroup.add(westWall);
        this.walls.west = westWall;

        // East wall (right) - positive X
        const eastWall = new THREE.Mesh(wallGeometry, createWallMaterial());
        eastWall.position.set(roomWidth / 2, roomHeight / 2, 0);
        eastWall.rotation.y = -Math.PI / 2;
        eastWall.receiveShadow = true;
        eastWall.userData.wallSide = 'east';
        roomGroup.add(eastWall);
        this.walls.east = eastWall;

        // Ceiling with subtle texture
        const ceilingMaterial = new THREE.MeshStandardMaterial({ 
            color: 0xfafafa,
            roughness: 0.95,
            metalness: 0.0
        });
        const ceiling = new THREE.Mesh(floorGeometry, ceilingMaterial);
        ceiling.rotation.x = Math.PI / 2;
        ceiling.position.y = roomHeight;
        ceiling.receiveShadow = true;
        roomGroup.add(ceiling);

        // Add grid helper on floor for reference (subtle)
        const gridHelper = new THREE.GridHelper(roomWidth, 20, 0xcccccc, 0xeeeeee);
        gridHelper.position.y = 0.01;
        roomGroup.add(gridHelper);

        this.scene.add(roomGroup);
        this.room = roomGroup;
    }
    
    updateWallTransparency() {
        if (!this.walls || !this.camera) return;
        
        // Get camera position relative to room center
        const cameraPos = this.camera.position;
        
        // Calculate which walls should be transparent based on camera position
        // A wall should be transparent if camera is on that side (looking through it)
        
        // North wall (back, z=-3): transparent if camera.z < 0
        if (this.walls.north) {
            const transparent = cameraPos.z < -0.5;
            this.walls.north.material.opacity = transparent ? 0.15 : 1.0;
        }
        
        // South wall (front, z=+3): transparent if camera.z > 0
        if (this.walls.south) {
            const transparent = cameraPos.z > 0.5;
            this.walls.south.material.opacity = transparent ? 0.15 : 1.0;
        }
        
        // West wall (left, x=-3): transparent if camera.x < 0
        if (this.walls.west) {
            const transparent = cameraPos.x < -0.5;
            this.walls.west.material.opacity = transparent ? 0.15 : 1.0;
        }
        
        // East wall (right, x=+3): transparent if camera.x > 0
        if (this.walls.east) {
            const transparent = cameraPos.x > 0.5;
            this.walls.east.material.opacity = transparent ? 0.15 : 1.0;
        }
    }

    addObject(mesh) {
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        this.scene.add(mesh);
        this.objects.push(mesh);
        return mesh;
    }

    removeObject(mesh) {
        const index = this.objects.indexOf(mesh);
        if (index > -1) {
            this.objects.splice(index, 1);
        }
        this.scene.remove(mesh);
        
        // Dispose geometry and materials
        if (mesh.geometry) mesh.geometry.dispose();
        if (mesh.material) {
            if (Array.isArray(mesh.material)) {
                mesh.material.forEach(mat => mat.dispose());
            } else {
                mesh.material.dispose();
            }
        }
    }

    clearAllObjects() {
        const objectsCopy = [...this.objects];
        objectsCopy.forEach(obj => this.removeObject(obj));
    }

    getObjectAtPosition(x, y) {
        const mouse = new THREE.Vector2(
            (x / this.renderer.domElement.clientWidth) * 2 - 1,
            -(y / this.renderer.domElement.clientHeight) * 2 + 1
        );

        const raycaster = new THREE.Raycaster();
        raycaster.setFromCamera(mouse, this.camera);

        const intersects = raycaster.intersectObjects(this.objects, true);
        
        if (intersects.length > 0) {
            let object = intersects[0].object;
            // Traverse up to find the main object
            while (object.parent && !this.objects.includes(object)) {
                object = object.parent;
            }
            return object;
        }
        return null;
    }

    getFloorPosition(x, y) {
        const mouse = new THREE.Vector2(
            (x / this.renderer.domElement.clientWidth) * 2 - 1,
            -(y / this.renderer.domElement.clientHeight) * 2 + 1
        );

        const raycaster = new THREE.Raycaster();
        raycaster.setFromCamera(mouse, this.camera);

        const intersects = raycaster.intersectObject(this.floor);
        
        if (intersects.length > 0) {
            return intersects[0].point;
        }
        return null;
    }

    onWindowResize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;

        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        
        this.controls.update();
        
        // Update wall transparency based on camera position
        this.updateWallTransparency();
        
        this.renderer.render(this.scene, this.camera);
    }

    dispose() {
        this.clearAllObjects();
        
        if (this.renderer) {
            this.renderer.dispose();
        }
        
        if (this.controls) {
            this.controls.dispose();
        }

        window.removeEventListener('resize', () => this.onWindowResize());
    }
}

// Export to global scope
window.ThreeScene = ThreeScene;
