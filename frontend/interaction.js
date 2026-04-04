/**
 * Interaction Manager for Feng Shui Room Designer
 * Handles object placement, selection, rotation, and deletion
 */

class InteractionManager {
    constructor(threeScene, objectLoader) {
        this.threeScene = threeScene;
        this.objectLoader = objectLoader;
        this.canvas = threeScene.renderer.domElement;
        
        this.selectedObject = null;
        this.isDragging = false;
        this.dragObject = null;
        this.dragPlane = null;
        this.offset = new THREE.Vector3();
        
        // Ghost mode tracking
        this.ghostObject = null;
        this.isGhostMode = false;
        
        // Double-click tracking
        this.lastClickTime = 0;
        this.doubleClickDelay = 300; // ms
        
        this.setupEventListeners();
        this.createDragPlane();
    }

    setupEventListeners() {
        this.canvas.addEventListener('click', (e) => this.onClick(e));
        this.canvas.addEventListener('dblclick', (e) => this.onDoubleClick(e));
        this.canvas.addEventListener('mousedown', (e) => this.onMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.onMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.onMouseUp(e));
        document.addEventListener('keydown', (e) => this.onKeyDown(e));
    }

    createDragPlane() {
        // Invisible plane at floor level for dragging
        const geometry = new THREE.PlaneGeometry(100, 100);
        const material = new THREE.MeshBasicMaterial({ 
            visible: false,
            side: THREE.DoubleSide
        });
        this.dragPlane = new THREE.Mesh(geometry, material);
        this.dragPlane.rotation.x = -Math.PI / 2;
        this.dragPlane.position.y = 0;
        this.threeScene.scene.add(this.dragPlane);
    }

    /**
     * Directly place object at a default position (one-click placement)
     * Creates object and places it immediately in the room without ghost mode.
     * Object is automatically selected and can be moved by dragging or double-clicking.
     * 
     * @param {string} objectType - Type of object to place (e.g., 'bed', 'sofa')
     * @param {Object} fengShuiData - Feng shui properties of the object
     * @returns {THREE.Object3D} The placed object
     */
    placeObjectDirectly(objectType, fengShuiData) {
        const object = this.objectLoader.loadObject(objectType, fengShuiData);
        
        // Calculate a default position (with slight randomization to avoid stacking)
        const randomOffset = () => (Math.random() - 0.5) * 2; // Random between -1 and 1
        const x = randomOffset();
        const z = randomOffset();
        
        object.position.set(x, 0, z);
        
        // Mark as placed (not ghost)
        object.userData.isGhost = false;
        object.userData.isFixed = true;
        
        // Add to scene and objects array
        this.threeScene.scene.add(object);
        this.threeScene.addObject(object);
        
        // Dispatch placement event
        const customEvent = new CustomEvent('objectPlaced', {
            detail: {
                type: object.userData.type,
                position: object.position.clone(),
                fengShui: object.userData.fengShui
            }
        });
        document.dispatchEvent(customEvent);
        
        // Automatically select the newly placed object
        this.selectObject(object);
        
        return object;
    }

    // Start ghost mode - object follows cursor until confirmed
    startGhostMode(objectType, fengShuiData) {
        // Clear any existing ghost object
        if (this.ghostObject) {
            this.cancelGhostMode();
        }
        
        const object = this.objectLoader.loadObject(objectType, fengShuiData);
        
        // Make it semi-transparent to indicate ghost mode
        object.traverse((child) => {
            if (child.material) {
                if (child.userData?.isSelectionProxy) {
                    // Keep helper hit meshes invisible even in ghost mode.
                    child.material.transparent = true;
                    child.material.opacity = 0.01;
                    child.material.depthWrite = false;
                    return;
                }
                if (!child.userData._originalMaterialState) {
                    child.userData._originalMaterialState = {
                        transparent: child.material.transparent,
                        opacity: child.material.opacity,
                        depthWrite: child.material.depthWrite
                    };
                }
                child.material.transparent = true;
                child.material.opacity = 0.6;
            }
        });
        
        // Add to scene
        this.threeScene.scene.add(object);
        
        // Set ghost mode
        this.ghostObject = object;
        this.isGhostMode = true;
        object.userData.isGhost = true;
        
        // Change cursor
        this.canvas.style.cursor = 'crosshair';
        
        // Disable orbit controls while in ghost mode
        this.threeScene.controls.enabled = false;
        
        // Show status message
        this.showGhostModeStatus(objectType);
        
        return object;
    }
    
    // Confirm ghost object placement
    confirmGhostPlacement() {
        if (!this.ghostObject || !this.isGhostMode) return;
        
        // Make object solid
        this.ghostObject.traverse((child) => {
            if (child.material) {
                if (child.userData?.isSelectionProxy) {
                    child.material.transparent = true;
                    child.material.opacity = 0.01;
                    child.material.depthWrite = false;
                    return;
                }

                const original = child.userData._originalMaterialState;
                if (original) {
                    child.material.transparent = original.transparent;
                    child.material.opacity = original.opacity;
                    child.material.depthWrite = original.depthWrite;
                } else {
                    child.material.opacity = 1.0;
                    child.material.transparent = false;
                }
            }
        });
        
        // Mark as placed
        this.ghostObject.userData.isGhost = false;
        this.ghostObject.userData.isFixed = true;
        
        // Add to objects array
        this.threeScene.addObject(this.ghostObject);
        
        // Dispatch placement event
        const customEvent = new CustomEvent('objectPlaced', {
            detail: {
                type: this.ghostObject.userData.type,
                position: this.ghostObject.position.clone(),
                fengShui: this.ghostObject.userData.fengShui
            }
        });
        document.dispatchEvent(customEvent);
        
        // Clear ghost mode
        this.ghostObject = null;
        this.isGhostMode = false;
        this.canvas.style.cursor = 'default';
        this.threeScene.controls.enabled = true;
        
        // Hide status message
        this.hideGhostModeStatus();
    }
    
    // Cancel ghost mode
    cancelGhostMode() {
        if (this.ghostObject) {
            this.threeScene.scene.remove(this.ghostObject);
            this.ghostObject = null;
        }
        this.isGhostMode = false;
        this.canvas.style.cursor = 'default';
        this.threeScene.controls.enabled = true;
        
        // Hide status message
        this.hideGhostModeStatus();
    }
    
    // Unlock a fixed object for repositioning
    unlockObject(object) {
        if (!object || !object.userData.isFixed) return;
        
        // Remove from objects array but keep in scene
        const index = this.threeScene.objects.indexOf(object);
        if (index > -1) {
            this.threeScene.objects.splice(index, 1);
        }
        
        // Convert to ghost mode
        object.traverse((child) => {
            if (child.material) {
                if (child.userData?.isSelectionProxy) {
                    child.material.transparent = true;
                    child.material.opacity = 0.01;
                    child.material.depthWrite = false;
                    return;
                }
                if (!child.userData._originalMaterialState) {
                    child.userData._originalMaterialState = {
                        transparent: child.material.transparent,
                        opacity: child.material.opacity,
                        depthWrite: child.material.depthWrite
                    };
                }
                child.material.transparent = true;
                child.material.opacity = 0.6;
            }
        });
        
        object.userData.isFixed = false;
        object.userData.isGhost = true;
        
        this.ghostObject = object;
        this.isGhostMode = true;
        this.canvas.style.cursor = 'crosshair';
        this.threeScene.controls.enabled = false;
        
        // Deselect if selected
        this.deselectObject();
        
        // Show status message for repositioning
        this.showGhostModeStatus(object.userData.type);
    }

    onClick(event) {
        // Ignore if in ghost mode (handled by double-click)
        if (this.isGhostMode) return;
        
        // Ignore if dragging
        if (this.isDragging) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        const clickedObject = this.threeScene.getObjectAtPosition(x, y);
        
        if (clickedObject && this.threeScene.objects.includes(clickedObject)) {
            this.selectObject(clickedObject);
        } else {
            this.deselectObject();
        }
    }
    
    onDoubleClick(event) {
        event.preventDefault();
        
        // If in ghost mode, confirm placement
        if (this.isGhostMode) {
            this.confirmGhostPlacement();
            return;
        }
        
        // Otherwise, check if clicking on a fixed object to unlock it
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        const clickedObject = this.threeScene.getObjectAtPosition(x, y);
        
        if (clickedObject && clickedObject.userData.isFixed) {
            this.unlockObject(clickedObject);
        }
    }

    onMouseDown(event) {
        // Don't handle mousedown during ghost mode
        if (this.isGhostMode) return;
        
        // Only left-click starts dragging
        if (!this.isDragging && event.button === 0) {
            const rect = this.canvas.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            
            const clickedObject = this.threeScene.getObjectAtPosition(x, y);
            const clickedType = clickedObject?.userData?.type;

            // Chandelier: allow immediate drag on click without requiring pre-selection.
            if (clickedObject && clickedType === 'chandelier') {
                if (this.selectedObject !== clickedObject) {
                    this.selectObject(clickedObject);
                }

                this.isDragging = true;
                this.dragObject = clickedObject;
                this.offset.set(0, 0, 0); // Center-follow drag for stability

                this.canvas.style.cursor = 'move';
                this.threeScene.controls.enabled = false;
                return;
            }

            // Existing behavior for all other objects: drag selected object.
            if (!this.selectedObject) return;

            // Chandelier has thin parts near the ceiling; allow drag when selected
            // even if exact click hit on sub-mesh misses.
            const selectedType = this.selectedObject.userData?.type;
            const isChandelierFallback = selectedType === 'chandelier' && clickedObject !== this.selectedObject;
            const canStartDrag = clickedObject === this.selectedObject || isChandelierFallback;

            if (canStartDrag) {
                this.isDragging = true;
                this.dragObject = this.selectedObject;
                this.offset.set(0, 0, 0);
                
                // Calculate offset
                const mouse = new THREE.Vector2(
                    (x / rect.width) * 2 - 1,
                    -(y / rect.height) * 2 + 1
                );
                
                const raycaster = new THREE.Raycaster();
                raycaster.setFromCamera(mouse, this.threeScene.camera);
                
                const intersects = raycaster.intersectObject(this.dragPlane);
                if (intersects.length > 0 && !isChandelierFallback) {
                    this.offset.copy(intersects[0].point).sub(this.dragObject.position);
                }
                
                this.canvas.style.cursor = 'move';
                this.threeScene.controls.enabled = false; // Disable orbit controls while dragging
            }
        }
    }

    onMouseMove(event) {
        // Handle ghost mode - object follows cursor
        if (this.isGhostMode && this.ghostObject) {
            event.preventDefault();
            
            const rect = this.canvas.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            
            const mouse = new THREE.Vector2(
                (x / rect.width) * 2 - 1,
                -(y / rect.height) * 2 + 1
            );
            
            const raycaster = new THREE.Raycaster();
            raycaster.setFromCamera(mouse, this.threeScene.camera);
            
            const intersects = raycaster.intersectObject(this.dragPlane);
            
            if (intersects.length > 0) {
                const point = intersects[0].point;
                
                // Update ghost object position to follow cursor
                this.ghostObject.position.x = point.x;
                this.ghostObject.position.z = point.z;
                this.ghostObject.position.y = 0;
                
                // Keep within room bounds accounting for object size
                this.constrainToRoom(this.ghostObject);
            }
            return;
        }
        
        // Handle regular dragging
        if (!this.isDragging || !this.dragObject) return;
        
        event.preventDefault();
        
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        const mouse = new THREE.Vector2(
            (x / rect.width) * 2 - 1,
            -(y / rect.height) * 2 + 1
        );
        
        const raycaster = new THREE.Raycaster();
        raycaster.setFromCamera(mouse, this.threeScene.camera);
        
        const intersects = raycaster.intersectObject(this.dragPlane);
        
        if (intersects.length > 0) {
            const point = intersects[0].point;

            // Chandelier follows cursor center for predictable movement.
            if (this.dragObject.userData?.type === 'chandelier') {
                this.dragObject.position.x = point.x;
                this.dragObject.position.z = point.z;
            } else {
                // Update object position
                this.dragObject.position.x = point.x - this.offset.x;
                this.dragObject.position.z = point.z - this.offset.z;
            }
            
            // Keep within room bounds accounting for object size
            this.constrainToRoom(this.dragObject);
            
            // Update selection outline if this is the selected object
            if (this.dragObject === this.selectedObject) {
                this.updateSelectionOutline(this.dragObject);
            }
        }
    }

    onMouseUp(event) {
        if (this.isDragging && this.dragObject) {
            // If this was a new placement, add to objects array
            if (!this.threeScene.objects.includes(this.dragObject)) {
                this.threeScene.addObject(this.dragObject);
                
                // Dispatch custom event for UI update
                const customEvent = new CustomEvent('objectPlaced', {
                    detail: {
                        type: this.dragObject.userData.type,
                        position: this.dragObject.position.clone(),
                        fengShui: this.dragObject.userData.fengShui
                    }
                });
                document.dispatchEvent(customEvent);
                
                // Select the newly placed object
                this.selectObject(this.dragObject);
            } else {
                // Dispatch update event for moved object
                const customEvent = new CustomEvent('objectMoved', {
                    detail: {
                        type: this.dragObject.userData.type,
                        position: this.dragObject.position.clone()
                    }
                });
                document.dispatchEvent(customEvent);
            }
        }
        
        this.isDragging = false;
        this.dragObject = null;
        this.canvas.style.cursor = 'default';
        this.threeScene.controls.enabled = true;
    }

    selectObject(object) {
        // Deselect previous
        if (this.selectedObject) {
            this.deselectObject();
        }
        
        this.selectedObject = object;
        
        // Add selection outline
        this.addSelectionOutline(object);
        
        // Dispatch selection event
        const customEvent = new CustomEvent('objectSelected', {
            detail: {
                type: object.userData.type,
                position: object.position.clone(),
                rotation: object.rotation.y,
                fengShui: object.userData.fengShui
            }
        });
        document.dispatchEvent(customEvent);
    }

    deselectObject() {
        if (this.selectedObject) {
            this.removeSelectionOutline(this.selectedObject);
            this.selectedObject = null;
            
            // Dispatch deselection event
            const customEvent = new CustomEvent('objectDeselected');
            document.dispatchEvent(customEvent);
        }
    }

    addSelectionOutline(object) {
        // Calculate bounding box in world space
        const box = new THREE.Box3().setFromObject(object);
        const size = box.getSize(new THREE.Vector3());
        const center = box.getCenter(new THREE.Vector3());
        
        // Create outline box
        const geometry = new THREE.BoxGeometry(size.x * 1.1, size.y * 1.1, size.z * 1.1);
        const edges = new THREE.EdgesGeometry(geometry);
        const lineMaterial = new THREE.LineBasicMaterial({ color: 0x00ff00, linewidth: 2 });
        const outline = new THREE.LineSegments(edges, lineMaterial);
        
        // Position in world space and add to scene (not as child of object)
        // This keeps the outline axis-aligned when object rotates
        outline.position.copy(center);
        outline.name = 'selectionOutline';
        outline.userData.parentObject = object; // Store reference to parent
        
        this.threeScene.scene.add(outline);
    }

    removeSelectionOutline(object) {
        // Find outline in scene (not as child of object)
        const outline = this.threeScene.scene.children.find(
            child => child.name === 'selectionOutline' && child.userData.parentObject === object
        );
        if (outline) {
            this.threeScene.scene.remove(outline);
            outline.geometry.dispose();
            outline.material.dispose();
        }
    }
    
    updateSelectionOutline(object) {
        // Recalculate bounding box and update outline position
        const outline = this.threeScene.scene.children.find(
            child => child.name === 'selectionOutline' && child.userData.parentObject === object
        );
        if (outline) {
            const box = new THREE.Box3().setFromObject(object);
            const size = box.getSize(new THREE.Vector3());
            const center = box.getCenter(new THREE.Vector3());
            
            // Update outline size if needed (for rotation)
            const currentSize = new THREE.Vector3();
            new THREE.Box3().setFromObject(outline).getSize(currentSize);
            
            // If size changed significantly, recreate the outline
            if (Math.abs(currentSize.x - size.x) > 0.01 || 
                Math.abs(currentSize.z - size.z) > 0.01) {
                this.removeSelectionOutline(object);
                this.addSelectionOutline(object);
            } else {
                // Just update position
                outline.position.copy(center);
            }
        }
    }

    rotateSelectedObject(angle = Math.PI / 4) {
        if (this.selectedObject) {
            this.selectedObject.rotation.y += angle;
            
            // Update selection outline to match new bounding box
            this.removeSelectionOutline(this.selectedObject);
            this.addSelectionOutline(this.selectedObject);
            
            // Constrain to room boundaries after rotation
            this.constrainToRoom(this.selectedObject);
            
            // Dispatch rotation event
            const customEvent = new CustomEvent('objectRotated', {
                detail: {
                    type: this.selectedObject.userData.type,
                    rotation: this.selectedObject.rotation.y
                }
            });
            document.dispatchEvent(customEvent);
        }
    }

    deleteSelectedObject() {
        if (this.selectedObject) {
            const objectToDelete = this.selectedObject;
            const deletedType = objectToDelete.userData.type;

            // Remove selection outline first to avoid leftover green wireframe.
            this.removeSelectionOutline(objectToDelete);

            this.threeScene.removeObject(objectToDelete);
            this.selectedObject = null;

            // Safety cleanup for any orphan outline in scene.
            const orphanOutlines = this.threeScene.scene.children.filter(
                child => child.name === 'selectionOutline'
            );
            orphanOutlines.forEach((outline) => {
                this.threeScene.scene.remove(outline);
                outline.geometry?.dispose?.();
                outline.material?.dispose?.();
            });
            
            // Dispatch deletion event
            const customEvent = new CustomEvent('objectDeleted', {
                detail: { type: deletedType }
            });
            document.dispatchEvent(customEvent);
        }
    }

    onKeyDown(event) {
        // Handle Enter key to confirm ghost placement
        if (event.key === 'Enter') {
            if (this.isGhostMode) {
                event.preventDefault();
                this.confirmGhostPlacement();
            }
            return;
        }
        
        // Handle Escape to cancel ghost mode
        if (event.key === 'Escape') {
            if (this.isGhostMode) {
                event.preventDefault();
                this.cancelGhostMode();
            }
            return;
        }
        
        // Other keys only work with selected object
        if (!this.selectedObject) return;
        
        switch(event.key) {
            case 'Delete':
            case 'Backspace':
                event.preventDefault();
                this.deleteSelectedObject();
                break;
            case 'r':
            case 'R':
                event.preventDefault();
                this.rotateSelectedObject(Math.PI / 4); // 45 degrees
                break;
            case 'ArrowLeft':
                event.preventDefault();
                this.selectedObject.position.x -= 0.1;
                this.constrainToRoom(this.selectedObject);
                this.updateSelectionOutline(this.selectedObject);
                break;
            case 'ArrowRight':
                event.preventDefault();
                this.selectedObject.position.x += 0.1;
                this.constrainToRoom(this.selectedObject);
                this.updateSelectionOutline(this.selectedObject);
                break;
            case 'ArrowUp':
                event.preventDefault();
                this.selectedObject.position.z -= 0.1;
                this.constrainToRoom(this.selectedObject);
                this.updateSelectionOutline(this.selectedObject);
                break;
            case 'ArrowDown':
                event.preventDefault();
                this.selectedObject.position.z += 0.1;
                this.constrainToRoom(this.selectedObject);
                this.updateSelectionOutline(this.selectedObject);
                break;
        }
    }

    clearAll() {
        this.deselectObject();
        
        // Cancel ghost mode if active
        if (this.isGhostMode) {
            this.cancelGhostMode();
        }
        
        this.threeScene.clearAllObjects();
        
        // Dispatch clear event
        const customEvent = new CustomEvent('allObjectsCleared');
        document.dispatchEvent(customEvent);
    }
    
    showGhostModeStatus(objectType) {
        // Create or update status indicator
        let statusDiv = document.getElementById('ghostModeStatus');
        
        if (!statusDiv) {
            statusDiv = document.createElement('div');
            statusDiv.id = 'ghostModeStatus';
            statusDiv.style.cssText = `
                position: fixed;
                top: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: linear-gradient(135deg, #00A99D 0%, #00c9ba 100%);
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                box-shadow: 0 4px 12px rgba(0, 169, 157, 0.3);
                z-index: 10000;
                animation: slideDown 0.3s ease-out;
            `;
            document.body.appendChild(statusDiv);
            
            // Add animation
            const style = document.createElement('style');
            style.textContent = `
                @keyframes slideDown {
                    from { transform: translateX(-50%) translateY(-20px); opacity: 0; }
                    to { transform: translateX(-50%) translateY(0); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }
        
        const capitalizedType = objectType.charAt(0).toUpperCase() + objectType.slice(1);
        statusDiv.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 18px;">👻</span>
                <span>Placing <strong>${capitalizedType}</strong></span>
                <span style="margin-left: 10px; opacity: 0.9; font-size: 12px;">Double-click or press Enter to confirm • Esc to cancel</span>
            </div>
        `;
        statusDiv.style.display = 'block';
    }
    
    hideGhostModeStatus() {
        const statusDiv = document.getElementById('ghostModeStatus');
        if (statusDiv) {
            statusDiv.style.display = 'none';
        }
    }
    
    constrainToRoom(object) {
        if (!object || !this.threeScene.roomDimensions) return;
        
        // Calculate object's bounding box
        const bbox = new THREE.Box3().setFromObject(object);
        const size = new THREE.Vector3();
        bbox.getSize(size);
        
        // Get room dimensions
        const roomWidth = this.threeScene.roomDimensions.width;
        const roomDepth = this.threeScene.roomDimensions.depth;
        
        // Calculate max positions accounting for object size
        // Room extends from -width/2 to +width/2, so subtract half object size
        const maxX = (roomWidth / 2) - (size.x / 2) - 0.1; // 0.1m safety margin
        const maxZ = (roomDepth / 2) - (size.z / 2) - 0.1;
        
        // Constrain position
        object.position.x = Math.max(-maxX, Math.min(maxX, object.position.x));
        object.position.z = Math.max(-maxZ, Math.min(maxZ, object.position.z));

        // Ceiling-mounted objects should stay attached to the ceiling plane.
        if (object.userData && object.userData.type === 'chandelier') {
            const roomHeight = this.threeScene.roomDimensions.height;
            const topGap = roomHeight - bbox.max.y;
            object.position.y += topGap;
        }

        // Keep windows wall-mounted and facing the room center so the outside view stays consistent.
        if (object.userData && object.userData.type === 'window') {
            this.alignWindowToNearestWall(object, roomWidth, roomDepth, size);
        }
    }

    alignWindowToNearestWall(object, roomWidth, roomDepth, size) {
        const wallInset = 0.04;
        const halfW = (roomWidth / 2) - (size.x / 2) - wallInset;
        const halfD = (roomDepth / 2) - (size.z / 2) - wallInset;

        const distToXWall = halfW - Math.abs(object.position.x);
        const distToZWall = halfD - Math.abs(object.position.z);

        if (distToXWall <= distToZWall) {
            // Snap to east/west wall.
            if (object.position.x >= 0) {
                object.position.x = halfW;
                object.rotation.y = -Math.PI / 2; // Face room center (-X)
            } else {
                object.position.x = -halfW;
                object.rotation.y = Math.PI / 2; // Face room center (+X)
            }
        } else {
            // Snap to north/south wall.
            if (object.position.z >= 0) {
                object.position.z = halfD;
                object.rotation.y = 0; // Face room center (-Z)
            } else {
                object.position.z = -halfD;
                object.rotation.y = Math.PI; // Face room center (+Z)
            }
        }

        // Safety net: ensure the window view plane always faces into the room.
        this.ensureWindowFacesInterior(object);
    }

    ensureWindowFacesInterior(object) {
        if (!object) return;

        let viewPlane = null;
        object.traverse((child) => {
            if (viewPlane) return;
            if (child.isMesh && (child.userData?.isWindowView || child.name === 'windowView')) {
                viewPlane = child;
            }
        });

        if (!viewPlane) return;

        object.updateMatrixWorld(true);

        const worldPos = new THREE.Vector3();
        viewPlane.getWorldPosition(worldPos);

        const toCenter = new THREE.Vector3(-worldPos.x, 0, -worldPos.z).normalize();

        const frontNormal = new THREE.Vector3(0, 0, 1)
            .applyQuaternion(viewPlane.getWorldQuaternion(new THREE.Quaternion()))
            .normalize();

        // If front face points away from room center, flip object.
        if (frontNormal.dot(toCenter) < 0) {
            object.rotation.y += Math.PI;
        }
    }

    getPlacedObjects() {
        return this.threeScene.objects.map(obj => ({
            type: obj.userData.type,
            position: obj.position.clone(),
            rotation: obj.rotation.y,
            fengShui: obj.userData.fengShui
        }));
    }

    dispose() {
        this.deselectObject();
        
        // Cancel ghost mode if active
        if (this.isGhostMode) {
            this.cancelGhostMode();
        }
        
        // Remove status indicator
        const statusDiv = document.getElementById('ghostModeStatus');
        if (statusDiv) {
            statusDiv.remove();
        }
        
        if (this.dragPlane) {
            this.threeScene.scene.remove(this.dragPlane);
            this.dragPlane.geometry.dispose();
            this.dragPlane.material.dispose();
        }
        
        document.removeEventListener('keydown', (e) => this.onKeyDown(e));
    }
}

// Export to global scope
window.InteractionManager = InteractionManager;
