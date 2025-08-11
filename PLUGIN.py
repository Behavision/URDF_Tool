import bpy
from bpy.types import Operator
from bpy.props import *
import bmesh
from mathutils import Vector
from bpy.props import BoolProperty, StringProperty, EnumProperty
from bpy.types import Operator, Panel, AddonPreferences

bl_info = {
    "name": "URDF Data Processor",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Toolbar > URDF Tools",
    "description": "Automated URDF data processing with Phobos integration",
    "warning": "",
    "doc_url": "",
    "category": "Import-Export",
}

class URDF_OT_ClearParentKeepTransform(Operator):
    """Clear parent and keep transform (Step 1)"""
    bl_idname = "urdf.clear_parent_keep_transform"
    bl_label = "Clear Parent Keep Transform"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        self.report({'INFO'}, "Cleared all parents, kept transforms")
        return {'FINISHED'}

class URDF_OT_DeleteNonMesh(Operator):
    """Delete all non-mesh objects (Step 2)"""
    bl_idname = "urdf.delete_non_mesh"
    bl_label = "Delete Non-Mesh Objects"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.context.scene.objects:
            if obj.type != 'MESH':
                obj.select_set(True)
        bpy.ops.object.delete()
        self.report({'INFO'}, "Deleted all non-mesh objects")
        return {'FINISHED'}

class URDF_OT_SetVisualMesh(Operator):
    """Set all objects as visual mesh type (Step 3)"""
    bl_idname = "urdf.set_visual_mesh"
    bl_label = "Set Visual Mesh"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
        
        if not mesh_objects:
            self.report({'WARNING'}, "场景中未找到网格对象")
            return {'CANCELLED'}
        
        print(f"\n{'='*60}")
        print(f"开始处理 {len(mesh_objects)} 个网格对象...")
        print(f"{'='*60}")
        
        success_count = 0
        
        for i, obj in enumerate(mesh_objects, 1):
            print(f"\n步骤 {i}/{len(mesh_objects)}: 处理 '{obj.name}'")
            
            try:
                # 激活对象
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                
                # 步骤1: 设置visual类型（保持原有代码不变）
                print(f"  1. 设置visual类型...")
                self.set_visual_type(obj)
                
                # 步骤2: 使用正确的方法设置geometry为mesh类型
                print(f"  2. 设置geometry为mesh类型...")
                self.set_geometry_mesh_type(obj)
                
                success_count += 1
                print(f"  ✅ '{obj.name}' 处理成功")
                    
            except Exception as e:
                print(f"  ❌ 处理 '{obj.name}' 失败: {e}")
        
        # 最终提示
        print(f"\n{'='*60}")
        print(f"处理完成: {success_count}/{len(mesh_objects)} 个对象")
        print(f"{'='*60}")
        
        if success_count > 0:
            self.report({'INFO'}, f"成功设置 {success_count} 个对象的geometry类型为mesh")
            print(f"\n完成! 成功设置 {success_count}/{len(mesh_objects)} 个对象")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "没有对象被成功设置")
            return {'CANCELLED'}
    
    def set_visual_type(self, obj):
        """设置visual类型（保持原有代码不变）"""
        try:
            if hasattr(bpy.ops.phobos, 'set_phobostype'):
                bpy.ops.phobos.set_phobostype(phobostype='visual')
            else:
                obj['phobostype'] = 'visual'
            print(f"    ✓ visual类型设置成功")
        except Exception as e:
            obj['phobostype'] = 'visual'
            print(f"    ✓ visual类型手动设置成功")
    
    def set_geometry_mesh_type(self, obj):
        """使用与参考代码完全一致的方法设置geometry/type为mesh"""
        try:
            # 设置geometry/type为mesh（与参考代码完全一致）
            obj['geometry/type'] = 'mesh'
            print(f"    ✅ '{obj.name}': geometry/type = 'mesh'")
            
        except Exception as e:
            print(f"    ❌ 设置 '{obj.name}' 失败: {e}")

class URDF_OT_SmartJoin(Operator):
    """Smart join selected objects (Step 4)"""
    bl_idname = "urdf.smart_join"
    bl_label = "Smart Join"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        selected = bpy.context.selected_objects
        if len(selected) > 1:
            bpy.context.view_layer.objects.active = selected[0]
            bpy.ops.object.join()
            self.report({'INFO'}, f"Joined {len(selected)} objects")
        else:
            self.report({'WARNING'}, "Need at least 2 objects selected")
        return {'FINISHED'}

class URDF_OT_CreateLinkAtSelection(Operator):
    """Set 3D cursor at geometric center of selected elements (Step 5)"""
    bl_idname = "urdf.create_link_at_selection"
    bl_label = "Set Cursor at Selection Center"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        if obj and obj.type == 'MESH' and obj.mode == 'EDIT':
            # Get bmesh representation
            bm = bmesh.from_edit_mesh(obj.data)
            
            # Get selected elements and calculate center
            selected_verts = []
            selected_edges = []
            selected_faces = []
            
            # Collect selected vertices
            for v in bm.verts:
                if v.select:
                    selected_verts.append(v)
            
            # Collect selected edges
            for e in bm.edges:
                if e.select:
                    selected_edges.append(e)
            
            # Collect selected faces
            for f in bm.faces:
                if f.select:
                    selected_faces.append(f)
            
            # Calculate geometric center based on selection
            center = Vector((0, 0, 0))
            count = 0
            
            if selected_faces:
                # If faces are selected, use face centers
                for face in selected_faces:
                    center += face.calc_center_median()
                    count += 1
                self.report({'INFO'}, f"Used {count} selected faces for center calculation")
                
            elif selected_edges:
                # If edges are selected, use edge midpoints
                for edge in selected_edges:
                    center += edge.verts[0].co + edge.verts[1].co
                    count += 2
                self.report({'INFO'}, f"Used {len(selected_edges)} selected edges for center calculation")
                
            elif selected_verts:
                # If only vertices are selected, use vertex positions
                for vert in selected_verts:
                    center += vert.co
                    count += 1
                self.report({'INFO'}, f"Used {count} selected vertices for center calculation")
            else:
                self.report({'WARNING'}, "No elements selected")
                return {'CANCELLED'}
            
            # Calculate average center
            if count > 0:
                center = center / count
                
                # Convert to world coordinates
                world_center = obj.matrix_world @ center
                
                # Set 3D cursor location
                context.scene.cursor.location = world_center
                
                self.report({'INFO'}, f"3D cursor set at selection center: ({world_center.x:.3f}, {world_center.y:.3f}, {world_center.z:.3f})")
                
                return {'FINISHED'}
            else:
                self.report({'WARNING'}, "No valid selection found")
                return {'CANCELLED'}
                
        else:
            self.report({'WARNING'}, "Must be in edit mode with mesh object selected")
            return {'CANCELLED'}

class URDF_OT_RelevantBones(Operator):
    """Create relevant bones for robot links (replaces Ctrl+P functionality)"""
    bl_idname = "urdf.relevant_bones"
    bl_label = "Relevant Bones"
    bl_description = "Set parent-child relationship: mesh can bind to link, link can bind to link"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        selected_objects = context.selected_objects
        
        # 验证选择数量
        if len(selected_objects) != 2:
            self.report({'WARNING'}, f"请选择两个对象，当前选择了 {len(selected_objects)} 个对象")
            return {'CANCELLED'}
        
        # 获取活动对象作为父对象，另一个作为子对象
        active_obj = context.active_object
        if active_obj not in selected_objects:
            self.report({'WARNING'}, "活动对象必须在选择的对象中")
            return {'CANCELLED'}
        
        child_obj = None
        for obj in selected_objects:
            if obj != active_obj:
                child_obj = obj
                break
        
        parent_obj = active_obj
        
        # 识别对象类型
        def is_link_object(obj):
            # 通过多种方式识别link对象
            if 'phobostype' in obj and obj['phobostype'] == 'link':
                return True
            if obj.name.startswith("link") or obj.name == "base_link":
                return True
            if hasattr(obj, 'phobostype') and obj.phobostype == 'link':
                return True
            return False
        
        def is_mesh_object(obj):
            # 识别mesh对象（非link的mesh对象）
            if obj.type != 'MESH':
                return False
            if is_link_object(obj):
                return False
            return True
        
        # 判断对象类型
        child_is_mesh = is_mesh_object(child_obj)
        child_is_link = is_link_object(child_obj)
        parent_is_link = is_link_object(parent_obj)
        
        print(f"子对象 {child_obj.name}: mesh={child_is_mesh}, link={child_is_link}")
        print(f"父对象 {parent_obj.name}: link={parent_is_link}")
        
        # 验证绑定规则
        valid_binding = False
        binding_type = ""
        
        if child_is_mesh and parent_is_link:
            valid_binding = True
            binding_type = "mesh → link"
        elif child_is_link and parent_is_link:
            valid_binding = True
            binding_type = "link → link"
        
        if not valid_binding:
            child_type = "mesh" if child_is_mesh else ("link" if child_is_link else "unknown")
            parent_type = "link" if parent_is_link else "non-link"
            self.report({'WARNING'}, 
                       f"不支持的绑定类型: {child_type} → {parent_type}。"
                       f"只允许 mesh→link 或 link→link 的绑定")
            return {'CANCELLED'}
        
        try:
            # 清除所有选择
            bpy.ops.object.select_all(action='DESELECT')
            
            # 选择子对象和父对象
            child_obj.select_set(True)
            parent_obj.select_set(True)
            # 确保父对象是活动对象
            context.view_layer.objects.active = parent_obj
            
            # 尝试使用Phobos操作
            try:
                if hasattr(bpy.ops.phobos, 'parent'):
                    bpy.ops.phobos.parent()
                    self.report({'INFO'}, 
                               f"成功建立 {binding_type} 关系: {child_obj.name} → {parent_obj.name}")
                    return {'FINISHED'}
            except Exception as e:
                print(f"Phobos parent操作失败: {e}")
            
            # 备用方案：使用标准Blender操作
            bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
            
            self.report({'INFO'}, 
                       f"成功建立 {binding_type} 关系: {child_obj.name} → {parent_obj.name}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"建立关系失败: {str(e)}")
            print(f"详细错误: {e}")
            return {'CANCELLED'}
    
    @classmethod
    def poll(cls, context):
        # 确保有两个对象被选中且有活动对象
        return (len(context.selected_objects) == 2 and 
                context.active_object is not None and
                context.active_object in context.selected_objects)

class URDF_OT_NameLinks(Operator):
    """Name links sequentially (link1, link2, link3...) (Step 6)"""
    bl_idname = "urdf.name_links"
    bl_label = "Name Links Sequentially"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # 查找所有以"new_link"开头的对象
        new_links = []
        for obj in bpy.context.scene.objects:
            if obj.name.startswith("new_link"):
                new_links.append(obj)
        
        if not new_links:
            self.report({'WARNING'}, "No new_link objects found")
            return {'CANCELLED'}
        
        # 按对象名称排序，确保命名的一致性
        new_links.sort(key=lambda x: x.name)
        
        # 按顺序重命名
        renamed_count = 0
        for i, link in enumerate(new_links, 1):
            old_name = link.name
            new_name = f"link{i}"
            link.name = new_name
            renamed_count += 1
            print(f"Renamed: {old_name} -> {new_name}")
        
        self.report({'INFO'}, f"Successfully renamed {renamed_count} links (link1 to link{renamed_count})")
        return {'FINISHED'}

class URDF_OT_CreateBaseLink(Operator):
    """Rename selected object to base_link (Step 7a)"""
    bl_idname = "urdf.create_base_link"
    bl_label = "Set Selected as Base Link"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # 获取选中的对象
        selected_objects = bpy.context.selected_objects
        
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}
        
        if len(selected_objects) > 1:
            self.report({'WARNING'}, "Please select only one object to be base_link")
            return {'CANCELLED'}
        
        selected_obj = selected_objects[0]
        
        # 检查是否已经存在base_link
        existing_base_link = None
        for obj in bpy.context.scene.objects:
            if obj.name == "base_link" and obj != selected_obj:
                existing_base_link = obj
                break
        
        if existing_base_link:
            # 如果已存在base_link，将其重命名
            old_name = existing_base_link.name
            existing_base_link.name = f"{old_name}_old"
            self.report({'WARNING'}, f"Existing base_link renamed to {existing_base_link.name}")
        
        # 重命名选中对象为base_link
        old_name = selected_obj.name
        selected_obj.name = "base_link"
        
        # 设置Phobos属性（如果可用）
        try:
            # 确保对象被激活
            bpy.context.view_layer.objects.active = selected_obj
            
            # 设置为link类型
            if self.check_phobos_availability():
                try:
                    if hasattr(bpy.ops, 'phobos') and hasattr(bpy.ops.phobos, 'define_phobostype'):
                        bpy.ops.phobos.define_phobostype(phobostype='link')
                    elif hasattr(bpy.ops, 'phobos') and hasattr(bpy.ops.phobos, 'set_phobostype'):
                        bpy.ops.phobos.set_phobostype(phobostype='link')
                except Exception as e:
                    print(f"Phobos操作失败: {e}")
            
            # 设置基本属性
            selected_obj['phobostype'] = 'link'
            selected_obj['link/name'] = 'base_link'
            
        except Exception as e:
            print(f"设置属性时出错: {e}")
        
        self.report({'INFO'}, f"Renamed '{old_name}' to 'base_link'")
        return {'FINISHED'}
    
    def check_phobos_availability(self):
        """检查Phobos是否可用"""
        try:
            if 'phobos' in bpy.context.preferences.addons:
                return True
            import phobos
            return True
        except:
            return False

class URDF_OT_ParentToBase(Operator):
    """将所有未绑定的网格板块和link绑定到base_link上 (Step 7b)"""
    bl_idname = "urdf.parent_to_base"
    bl_label = "Parent Unbound Objects to Base"
    bl_description = "将所有未绑定link的网格板块以及所有其他link绑定到base_link上"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # 查找base_link对象
        base_link = self.find_base_link()
        
        if not base_link:
            self.report({'ERROR'}, "未找到base_link对象，请先创建base_link")
            return {'CANCELLED'}
        
        try:
            print(f"\n{'='*50}")
            print(f"开始将未绑定对象绑定到base_link...")
            print(f"base_link对象: {base_link.name}")
            print(f"{'='*50}")
            
            # 查找需要绑定的对象
            objects_to_bind = self.find_objects_to_bind(base_link)
            
            if not objects_to_bind:
                self.report({'INFO'}, "没有找到需要绑定的未绑定对象")
                return {'FINISHED'}
            
            # 执行绑定操作
            success_count = self.bind_objects_to_base(objects_to_bind, base_link)
            
            # 报告结果
            total_objects = len(objects_to_bind)
            self.report({'INFO'}, f"成功将 {success_count}/{total_objects} 个对象绑定到base_link")
            
            print(f"\n✓ 绑定完成: {success_count}/{total_objects} 个对象")
            print(f"{'='*50}\n")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"绑定过程失败: {str(e)}")
            print(f"绑定错误: {e}")
            return {'CANCELLED'}
    
    def find_base_link(self):
        """查找base_link对象"""
        for obj in bpy.context.scene.objects:
            if obj.name == "base_link":
                return obj
        return None
    
    def find_objects_to_bind(self, base_link):
        """查找需要绑定的对象"""
        objects_to_bind = []
        
        print("搜索需要绑定的对象...")
        
        for obj in bpy.context.scene.objects:
            # 跳过base_link自身
            if obj == base_link:
                continue
                
            # 只处理没有父对象的对象
            if obj.parent is not None:
                continue
            
            should_bind = False
            obj_type_description = ""
            
            # 条件1: 网格对象且未绑定link
            if obj.type == 'MESH' and not self.is_link_object(obj):
                should_bind = True
                obj_type_description = "未绑定link的网格"
            
            # 条件2: 其他link对象（非base_link）
            elif self.is_link_object(obj):
                should_bind = True
                obj_type_description = "link对象"
            
            if should_bind:
                objects_to_bind.append(obj)
                print(f"  → 添加: {obj.name} ({obj_type_description})")
        
        print(f"找到 {len(objects_to_bind)} 个需要绑定的对象")
        return objects_to_bind
    
    def is_link_object(self, obj):
        """判断对象是否为link对象"""
        # 检查phobostype属性
        if 'phobostype' in obj and obj['phobostype'] == 'link':
            return True
        
        # 检查名称模式
        if obj.name.startswith("link") or obj.name == "base_link":
            return True
            
        # 检查是否有link相关属性
        for key in obj.keys():
            if key.startswith('link/'):
                return True
        
        return False
    
    def bind_objects_to_base(self, objects_to_bind, base_link):
        """将对象绑定到base_link"""
        success_count = 0
        
        print(f"\n开始绑定操作...")
        
        for obj in objects_to_bind:
            try:
                print(f"  绑定: {obj.name} → {base_link.name}")
                
                # 清除当前选择
                bpy.ops.object.select_all(action='DESELECT')
                
                # 选择要绑定的对象和base_link
                obj.select_set(True)
                base_link.select_set(True)
                
                # 设置base_link为活动对象
                bpy.context.view_layer.objects.active = base_link
                
                # 尝试使用Phobos的parent方法（如果可用）
                binding_success = False
                
                # 方法1: 尝试Phobos parent
                if self.try_phobos_parent():
                    binding_success = True
                    print(f"    ✓ 使用Phobos方法绑定成功")
                
                # 方法2: 使用标准Blender parent
                if not binding_success:
                    try:
                        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
                        binding_success = True
                        print(f"    ✓ 使用标准方法绑定成功")
                    except Exception as e:
                        print(f"    ✗ 标准方法绑定失败: {e}")
                
                # 验证绑定结果
                if binding_success and obj.parent == base_link:
                    success_count += 1
                    print(f"    ✓ 验证成功: {obj.name} 已绑定到 {base_link.name}")
                else:
                    print(f"    ✗ 绑定验证失败: {obj.name}")
                
            except Exception as e:
                print(f"    ✗ 绑定 {obj.name} 失败: {e}")
                continue
        
        return success_count
    
    def try_phobos_parent(self):
        """尝试使用Phobos的parent方法"""
        try:
            if hasattr(bpy.ops.phobos, 'parent'):
                bpy.ops.phobos.parent()
                return True
        except Exception as e:
            print(f"    Phobos parent方法失败: {e}")
        return False
    
    @classmethod
    def poll(cls, context):
        # 确保场景中有对象
        return len(bpy.context.scene.objects) > 0

class URDF_OT_SetModuleRoot(Operator):
    """设置模型根目录并命名为URDF_Data (Step 8) - 针对base_link对象"""
    bl_idname = "urdf.set_module_root"
    bl_label = "Set Model Root & Name (base_link)"
    bl_description = "对名为base_link的对象执行Set Model Root和Name Model操作"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        try:
            print(f"\n{'='*60}")
            print("开始执行Step 8: 设置base_link为模型根并命名...")
            print(f"{'='*60}")
            
            # 检查Phobos可用性
            if not self.check_phobos_available():
                self.report({'ERROR'}, "Phobos插件不可用，请确保已安装并启用Phobos")
                return {'CANCELLED'}
            
            # 查找base_link对象
            base_link = self.find_base_link()
            if not base_link:
                self.report({'ERROR'}, "未找到名为'base_link'的对象")
                return {'CANCELLED'}
            
            # 修复base_link的变换问题（如果需要）
            print("步骤0: 检查并修复base_link变换...")
            self.fix_base_link_transform(base_link)
            
            # 确保选择base_link
            self.select_base_link(base_link)
            
            # 步骤1: 设置base_link为模型根
            print(f"步骤1: 设置base_link为模型根...")
            if not self.set_model_root_for_base_link(base_link):
                print("    Set Model Root可能失败，但继续执行...")
            
            # 步骤2: 设置模型名称为URDF_Data
            print("步骤2: 设置模型名称为URDF_Data...")
            if not self.set_model_name("URDF_Data"):
                print("    Name Model可能失败，但操作已尝试...")
            
            # 显示最终状态
            self.show_final_status(base_link)
            
            self.report({'INFO'}, "base_link操作完成")
            print(f"✓ Step 8 完成")
            print(f"{'='*60}\n")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Step 8 操作失败: {str(e)}")
            print(f"Step 8 错误详情: {e}")
            return {'CANCELLED'}
    
    def check_phobos_available(self):
        """检查Phobos是否可用"""
        try:
            if not hasattr(bpy.ops, 'phobos'):
                print("  ✗ Phobos操作符不可用")
                return False
                
            print("  ✓ Phobos插件可用")
            return True
            
        except Exception as e:
            print(f"  检查Phobos失败: {e}")
            return False
    
    def find_base_link(self):
        """查找名为base_link的对象"""
        print("  查找base_link对象...")
        
        base_link = None
        
        # 查找名为base_link的对象
        for obj in bpy.context.scene.objects:
            if obj.name == "base_link":
                base_link = obj
                print(f"  ✓ 找到base_link: {obj.name} (类型: {obj.type})")
                break
        
        if base_link is None:
            print("  ✗ 未找到名为'base_link'的对象")
        
        return base_link
    
    def fix_base_link_transform(self, base_link):
        """修复base_link的变换问题（如果需要）"""
        try:
            scale = base_link.scale
            location = base_link.location
            rotation = base_link.rotation_euler
            
            # 检查是否有负缩放或异常值
            has_negative_scale = any(s < 0 for s in scale)
            has_large_values = (
                any(abs(s) > 1000 for s in scale) or
                any(abs(l) > 1000 for l in location) or
                any(abs(r) > 100 for r in rotation)
            )
            
            if has_negative_scale or has_large_values:
                print(f"    检测到异常变换，进行修复:")
                print(f"      scale: {scale}")
                print(f"      location: {location}")
                print(f"      rotation: {rotation}")
                
                # 应用变换
                old_active = bpy.context.view_layer.objects.active
                bpy.ops.object.select_all(action='DESELECT')
                base_link.select_set(True)
                bpy.context.view_layer.objects.active = base_link
                
                bpy.ops.object.transform_apply(
                    location=True, 
                    rotation=True, 
                    scale=True
                )
                
                # 重置缩放
                base_link.scale = (1.0, 1.0, 1.0)
                
                # 恢复原来的选择
                if old_active:
                    bpy.context.view_layer.objects.active = old_active
                
                print(f"      ✓ base_link变换已修复")
            else:
                print(f"    ✓ base_link变换正常")
            
        except Exception as e:
            print(f"    修复base_link变换失败: {e}")
    
    def select_base_link(self, base_link):
        """选择base_link对象"""
        try:
            # 清除所有选择
            bpy.ops.object.select_all(action='DESELECT')
            
            # 选择base_link
            base_link.select_set(True)
            bpy.context.view_layer.objects.active = base_link
            
            print(f"    ✓ 已选择base_link")
            return True
                
        except Exception as e:
            print(f"    选择base_link失败: {e}")
            return False
    
    def set_model_root_for_base_link(self, base_link):
        """为base_link执行Set Model Root操作"""
        try:
            print(f"    调用 bpy.ops.phobos.set_model_root()...")
            
            # 确保base_link被选中
            base_link.select_set(True)
            bpy.context.view_layer.objects.active = base_link
            bpy.context.view_layer.update()
            
            # 调用Phobos的set_model_root操作
            if hasattr(bpy.ops.phobos, 'set_model_root'):
                result = bpy.ops.phobos.set_model_root()
                print(f"    Set Model Root 结果: {result}")
                
                # 无论结果如何，都认为尝试成功了
                print(f"    ✓ Set Model Root 操作已执行")
                return True
            else:
                print(f"    ! set_model_root 操作符不存在，尝试手动设置...")
                return self.manual_set_model_root(base_link)
                
        except Exception as e:
            error_msg = str(e)
            print(f"    Set Model Root 遇到异常: {e}")
            
            # 如果是scipy相关错误，尝试手动设置
            if "from_dcm" in error_msg or "scipy" in error_msg or "matrix" in error_msg:
                print(f"    检测到变换矩阵问题，尝试手动设置...")
                return self.manual_set_model_root(base_link)
            else:
                print(f"    ✗ Set Model Root 失败")
                return False
    
    def manual_set_model_root(self, base_link):
        """手动设置base_link为模型根"""
        try:
            print("      手动设置base_link为模型根...")
            
            # 设置phobos属性
            base_link["phobostype"] = "link"
            base_link["phobos/is_root"] = True
            
            # 确保其他对象不是root（可选）
            for obj in bpy.context.scene.objects:
                if obj != base_link and obj.get('phobostype') == 'link':
                    obj["phobos/is_root"] = False
            
            print("      ✓ 手动设置base_link为模型根完成")
            return True
            
        except Exception as e:
            print(f"      ✗ 手动设置失败: {e}")
            return False
    
    def set_model_name(self, model_name):
        """设置模型名称"""
        try:
            print(f"    调用 bpy.ops.phobos.name_model(modelname='{model_name}')...")
            
            # 调用Phobos的name_model操作
            if hasattr(bpy.ops.phobos, 'name_model'):
                result = bpy.ops.phobos.name_model(modelname=model_name)
                print(f"    Name Model 结果: {result}")
                
                # 验证是否成功
                if self.verify_model_name(model_name):
                    print(f"    ✓ 模型名称设置成功: {model_name}")
                    return True
                else:
                    print(f"    ! 模型名称可能未设置成功，尝试备用方法...")
                    return self.set_model_name_fallback(model_name)
            else:
                print(f"    ! name_model 操作符不存在，尝试备用方法...")
                return self.set_model_name_fallback(model_name)
                
        except Exception as e:
            print(f"    Name Model 遇到异常: {e}")
            return self.set_model_name_fallback(model_name)
    
    def set_model_name_fallback(self, model_name):
        """备用方法：手动设置模型名称"""
        try:
            print(f"      尝试备用方法设置模型名称...")
            
            scene = bpy.context.scene
            success = False
            
            # 尝试多种设置方法
            try:
                if hasattr(scene, 'phobos'):
                    scene.phobos.modelname = model_name
                    print(f"        ✓ scene.phobos.modelname = '{model_name}'")
                    success = True
            except:
                pass
            
            try:
                if hasattr(scene, 'phobosexportsettings'):
                    export_settings = scene.phobosexportsettings
                    if hasattr(export_settings, 'modelname'):
                        export_settings.modelname = model_name
                        print(f"        ✓ export_settings.modelname = '{model_name}'")
                        success = True
                    if hasattr(export_settings, 'name'):
                        export_settings.name = model_name
                        print(f"        ✓ export_settings.name = '{model_name}'")
                        success = True
            except:
                pass
            
            if success:
                print(f"      ✓ 备用方法设置成功")
            else:
                print(f"      ! 备用方法也无法设置")
            
            return success
            
        except Exception as e:
            print(f"      ✗ 备用方法失败: {e}")
            return False
    
    def verify_model_name(self, expected_name):
        """验证模型名称是否设置成功"""
        try:
            scene = bpy.context.scene
            found_names = []
            
            # 检查各种可能的位置
            if hasattr(scene, 'phobos') and hasattr(scene.phobos, 'modelname'):
                if scene.phobos.modelname == expected_name:
                    found_names.append('scene.phobos.modelname')
            
            if hasattr(scene, 'phobosexportsettings'):
                export_settings = scene.phobosexportsettings
                if hasattr(export_settings, 'modelname') and export_settings.modelname == expected_name:
                    found_names.append('export_settings.modelname')
                if hasattr(export_settings, 'name') and export_settings.name == expected_name:
                    found_names.append('export_settings.name')
            
            return len(found_names) > 0
            
        except Exception as e:
            print(f"        验证模型名称失败: {e}")
            return False
    
    def show_final_status(self, base_link):
        """显示最终状态"""
        print(f"\n最终状态:")
        
        try:
            # base_link状态
            is_root = base_link.get('phobos/is_root', False)
            phobos_type = base_link.get('phobostype', 'None')
            print(f"  base_link:")
            print(f"    - phobostype: {phobos_type}")
            print(f"    - is_root: {is_root}")
            
            # 模型名称状态
            scene = bpy.context.scene
            model_names = []
            
            if hasattr(scene, 'phobos') and hasattr(scene.phobos, 'modelname'):
                model_names.append(f"scene.phobos.modelname = '{scene.phobos.modelname}'")
            
            if hasattr(scene, 'phobosexportsettings'):
                export_settings = scene.phobosexportsettings
                if hasattr(export_settings, 'modelname'):
                    model_names.append(f"export_settings.modelname = '{export_settings.modelname}'")
            
            print(f"  模型名称:")
            for name_info in model_names:
                print(f"    - {name_info}")
            
            if not model_names:
                print(f"    - 未找到模型名称设置")
            
        except Exception as e:
            print(f"  显示状态失败: {e}")
    
    @classmethod
    def poll(cls, context):
        # 确保场景中有名为base_link的对象
        return any(obj.name == "base_link" for obj in bpy.context.scene.objects)

class URDF_OT_SelectExportPathAndExport(Operator):
    """选择导出路径并执行Phobos导出 (替代原9b功能)"""
    bl_idname = "urdf.select_export_path_and_export"
    bl_label = "Select Export Path & Export URDF"
    bl_description = "选择导出路径并使用Phobos导出URDF模型"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 文件路径属性
    filepath: StringProperty(
        name="Export Path",
        description="Choose export directory",
        subtype='DIR_PATH'
    )
    
    # 导出选项
    export_urdf: BoolProperty(
        name="Export URDF",
        description="Export URDF format",
        default=True
    )
    
    export_joint_limits: BoolProperty(
        name="Export Joint Limits", 
        description="Export joint limits",
        default=True
    )
    
    mesh_format: EnumProperty(
        name="Mesh Format",
        description="Mesh export format",
        items=[
            ('dae', 'DAE (Collada)', 'Export meshes as DAE format'),
            ('stl', 'STL', 'Export meshes as STL format'),
            ('obj', 'OBJ', 'Export meshes as OBJ format'),
        ],
        default='dae'
    )
    
    model_name: StringProperty(
        name="Model Name",
        description="Name for the exported model",
        default="robot_model"
    )
    
    def execute(self, context):
        try:
            print(f"\n{'='*60}")
            print("开始Phobos URDF导出流程...")
            print(f"导出路径: {self.filepath}")
            print(f"模型名称: {self.model_name}")
            print(f"导出格式: URDF={self.export_urdf}, Joint Limits={self.export_joint_limits}")
            print(f"网格格式: {self.mesh_format}")
            print(f"{'='*60}")
            
            # 检查Phobos可用性
            if not self.check_phobos_available():
                self.report({'ERROR'}, "Phobos插件不可用")
                return {'CANCELLED'}
            
            # 检查是否有模型
            if not self.check_model_exists():
                self.report({'ERROR'}, "未找到URDF模型，请确保场景中有正确的机器人模型")
                return {'CANCELLED'}
            
            # 配置导出设置
            success = self.configure_export_settings(context)
            if not success:
                self.report({'ERROR'}, "导出设置配置失败")
                return {'CANCELLED'}
            
            # 执行导出
            export_result = self.execute_phobos_export(context)
            
            if export_result:
                self.report({'INFO'}, f"URDF导出完成: {self.filepath}")
                print(f"✓ 导出成功完成到: {self.filepath}")
                return {'FINISHED'}
            else:
                self.report({'WARNING'}, "导出可能不完整，请检查输出路径和文件")
                return {'FINISHED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"导出失败: {str(e)}")
            print(f"导出错误详情: {e}")
            return {'CANCELLED'}
    
    def check_phobos_available(self):
        """检查Phobos是否可用"""
        try:
            if not hasattr(bpy.ops, 'phobos'):
                print("  ✗ Phobos操作符不可用")
                return False
                
            if not hasattr(bpy.ops.phobos, 'export_model'):
                print("  ✗ export_model操作符不可用")
                return False
                
            scene = bpy.context.scene
            if not hasattr(scene, 'phobosexportsettings'):
                print("  ✗ phobosexportsettings不可用") 
                return False
                
            print("  ✓ Phobos导出组件检查完成")
            return True
            
        except Exception as e:
            print(f"  检查Phobos失败: {e}")
            return False
    
    def check_model_exists(self):
        """检查是否存在URDF模型"""
        try:
            # 查找根对象（base_link或其他link对象）
            root_obj = self.find_root_object()
            if root_obj:
                print(f"  ✓ 找到模型根对象: {root_obj.name}")
                return True
            
            # 检查是否有任何phobos类型的对象
            phobos_objects = []
            for obj in bpy.context.scene.objects:
                if obj.get('phobostype') in ['link', 'joint', 'motor', 'sensor']:
                    phobos_objects.append(obj.name)
            
            if phobos_objects:
                print(f"  ✓ 找到Phobos对象: {len(phobos_objects)}个")
                return True
            else:
                print("  ✗ 未找到URDF/Phobos模型对象")
                return False
                
        except Exception as e:
            print(f"  检查模型失败: {e}")
            return False
    
    def find_root_object(self):
        """查找根对象（base_link或模型根）"""
        # 首先查找base_link
        for obj in bpy.context.scene.objects:
            if obj.name.lower() == "base_link":
                return obj
        
        # 查找具有link类型且没有父对象的对象
        for obj in bpy.context.scene.objects:
            if (obj.get('phobostype') == 'link' and 
                obj.parent is None):
                return obj
        
        # 查找名称包含root、base的对象
        for obj in bpy.context.scene.objects:
            if any(keyword in obj.name.lower() for keyword in ['root', 'base']):
                return obj
        
        return None
    
    def configure_export_settings(self, context):
        """配置导出设置"""
        try:
            scene = context.scene
            export_settings = scene.phobosexportsettings
            
            print("  配置导出设置...")
            
            # 设置导出路径
            if self.filepath:
                export_settings.path = self.filepath
                print(f"    ✓ 导出路径: {self.filepath}")
            
            # 设置模型名称
            if self.model_name:
                export_settings.name = self.model_name
                export_settings.rosPackageName = self.model_name
                print(f"    ✓ 模型名称: {self.model_name}")
            
            # 调用updateExportPath方法（如果存在）
            if hasattr(export_settings, 'updateExportPath'):
                try:
                    export_settings.updateExportPath(context)
                    print(f"    ✓ 已更新导出路径设置")
                except Exception as e:
                    print(f"    ! updateExportPath调用失败: {e}")
            
            # 设置导出格式 - models
            scene.export_entity_urdf = self.export_urdf
            scene.export_entity_joint_limits = self.export_joint_limits
            scene.export_entity_sdf = False  # 禁用SDF
            scene.export_entity_smurf = False  # 禁用SMURF
            
            print(f"    ✓ Model格式: URDF={self.export_urdf}, Joint Limits={self.export_joint_limits}")
            
            # 设置网格格式
            if hasattr(export_settings, 'export_urdf_mesh_type'):
                export_settings.export_urdf_mesh_type = self.mesh_format
                print(f"    ✓ URDF mesh格式: {self.mesh_format}")
            
            # 设置mesh导出选项
            scene.export_mesh_dae = (self.mesh_format == 'dae')
            scene.export_mesh_stl = (self.mesh_format == 'stl')  
            scene.export_mesh_obj = (self.mesh_format == 'obj')
            
            print(f"    ✓ Mesh导出: DAE={self.mesh_format=='dae'}, STL={self.mesh_format=='stl'}, OBJ={self.mesh_format=='obj'}")
            
            # 设置路径类型为相对路径
            export_settings.urdfOutputPathtype = 'relative'
            if hasattr(export_settings, 'sdfOutputPathtype'):
                export_settings.sdfOutputPathtype = 'relative'
            
            print(f"    ✓ 输出路径类型: relative")
            
            print("  ✓ 导出设置配置完成")
            return True
            
        except Exception as e:
            print(f"  ✗ 配置导出设置失败: {e}")
            return False
    
    def execute_phobos_export(self, context):
        """执行Phobos导出"""
        try:
            print("  执行Phobos导出...")
            
            # 确保有选中的根对象
            root_object = self.find_root_object()
            if root_object:
                # 清除所有选择
                bpy.ops.object.select_all(action='DESELECT')
                # 选择并激活根对象
                bpy.context.view_layer.objects.active = root_object
                root_object.select_set(True)
                print(f"    使用根对象: {root_object.name}")
            
            # 调用Phobos导出
            print("    调用 bpy.ops.phobos.export_model()...")
            result = bpy.ops.phobos.export_model()
            
            if result == {'FINISHED'}:
                print("    ✓ Phobos export_model 执行成功")
                return True
            else:
                print(f"    ! Phobos export_model 返回: {result}")
                # 即使返回不是FINISHED，也可能成功了，检查文件是否存在
                import os
                if self.filepath and os.path.exists(self.filepath):
                    urdf_files = [f for f in os.listdir(self.filepath) if f.endswith('.urdf')]
                    if urdf_files:
                        print(f"    ✓ 发现导出的URDF文件: {urdf_files}")
                        return True
                return False
                
        except Exception as e:
            print(f"    ✗ Phobos导出执行失败: {e}")
            
            # 尝试备用导出方法
            try:
                print("    尝试备用导出方法...")
                if hasattr(bpy.ops.phobos, 'export_scene'):
                    result = bpy.ops.phobos.export_scene()
                    print(f"    备用方法结果: {result}")
                    return result == {'FINISHED'}
            except Exception as e2:
                print(f"    备用导出方法也失败: {e2}")
            
            return False
    
    def invoke(self, context, event):
        # 设置默认路径
        import os
        default_path = os.path.join(os.path.expanduser("~"), "Documents", "URDF_Export")
        self.filepath = default_path
        
        # 尝试从现有设置获取模型名称
        try:
            scene = context.scene
            if hasattr(scene, 'phobosexportsettings'):
                export_settings = scene.phobosexportsettings
                if export_settings.rosPackageName:
                    self.model_name = export_settings.rosPackageName
                elif export_settings.name:
                    self.model_name = export_settings.name
        except:
            pass
        
        # 打开文件浏览器
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def draw(self, context):
        layout = self.layout
        
        # 标题
        layout.label(text="Phobos URDF Export Settings", icon='EXPORT')
        layout.separator()
        
        # 路径设置
        box = layout.box()
        box.label(text="Export Path:", icon='FOLDER_REDIRECT')
        box.prop(self, "filepath", text="Directory")
        
        # 模型设置
        box = layout.box()
        box.label(text="Model Settings:", icon='OBJECT_DATA')
        box.prop(self, "model_name", text="Model Name")
        
        layout.separator()
        
        # 导出格式设置
        box = layout.box()
        box.label(text="Export Formats:", icon='SETTINGS')
        
        col = box.column(align=True)
        col.prop(self, "export_urdf", icon='FILE_TEXT')
        col.prop(self, "export_joint_limits", icon='CONSTRAINT')
        
        box.separator()
        
        # 网格格式
        box.label(text="Mesh Format:")
        box.prop(self, "mesh_format", expand=True)
        
        layout.separator()
        
        # 信息提示
        info_box = layout.box()
        info_box.label(text="Export Info:", icon='INFO')
        col = info_box.column(align=True)
        col.scale_y = 0.8
        col.label(text="• URDF file and meshes will be exported")
        col.label(text="• Make sure model has proper phobos setup")
        col.label(text="• Check export path after completion")

class URDF_OT_SetExportSettings(Operator):
    """Set URDF export settings - 配置导出model类型和mesh类型 (Step 10)"""
    bl_idname = "urdf.set_export_settings"
    bl_label = "Set Export Settings"
    bl_description = "配置Phobos导出设置：选择urdf, joint_limits格式，并设置mesh类型为dae"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        try:
            print(f"\n{'='*50}")
            print("配置Phobos导出设置...")
            print("- 启用：urdf, joint_limits")  
            print("- 设置：URDF mesh type = dae")
            print(f"{'='*50}")
            
            # 检查Phobos可用性
            if not self.check_phobos_available():
                self.report({'ERROR'}, "Phobos插件未启用或不可用")
                return {'CANCELLED'}
            
            # 同时配置model类型和mesh类型
            model_success = self.configure_export_models()
            mesh_success = self.configure_mesh_settings()
            
            total_success = model_success + mesh_success
            
            if total_success > 0:
                self.report({'INFO'}, "导出设置完成：urdf+joint_limits, mesh=dae")
                print(f"\n✓ 配置完成：设置了 {total_success} 项")
                print("请在3D视窗侧边栏Phobos>Export面板中确认设置")
                return {'FINISHED'}
            else:
                self.report({'WARNING'}, "请手动在Phobos Export面板中设置")
                return {'FINISHED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"配置失败: {str(e)}")
            print(f"详细错误: {e}")
            return {'CANCELLED'}
    
    def check_phobos_available(self):
        """检查Phobos是否可用"""
        try:
            if not hasattr(bpy.ops, 'phobos') or not hasattr(bpy.ops.phobos, 'export_model'):
                print("  ✗ Phobos插件不可用")
                return False
                
            scene = bpy.context.scene
            if not hasattr(scene, 'phobosexportsettings'):
                print("  ✗ phobosexportsettings不可用")
                return False
                
            print("  ✓ Phobos检查完成")
            return True
            
        except Exception as e:
            print(f"  检查失败: {e}")
            return False
    
    def configure_export_models(self):
        """配置导出model类型"""
        success = 0
        scene = bpy.context.scene
        
        print("  配置model导出格式...")
        
        # 设置Scene的直接导出属性
        model_settings = {
            'export_entity_urdf': True,        # 启用URDF导出
            'export_entity_joint_limits': True, # 启用joint_limits
            'export_entity_sdf': False,        # 禁用SDF
            'export_entity_smurf': False,      # 禁用SMURF
        }
        
        for attr_name, value in model_settings.items():
            try:
                if hasattr(scene, attr_name):
                    setattr(scene, attr_name, value)
                    status = "启用" if value else "禁用"
                    print(f"    {status}: {attr_name}")
                    success += 1
                    
            except Exception as e:
                print(f"    设置 {attr_name} 失败: {e}")
            
        return success
    
    def configure_mesh_settings(self):
        """配置mesh导出设置，特别是URDF mesh type"""
        success = 0
        scene = bpy.context.scene
        
        print("  配置mesh导出格式...")
        
        try:
            export_settings = scene.phobosexportsettings
            
            # 关键设置：URDF mesh type = dae
            if hasattr(export_settings, 'export_urdf_mesh_type'):
                export_settings.export_urdf_mesh_type = 'dae'
                print(f"    ✓ 设置: export_urdf_mesh_type = 'dae'")
                success += 1
            else:
                print(f"    ✗ 未找到 export_urdf_mesh_type 属性")
            
            # 可选：同时设置SDF mesh type为dae（虽然我们不用SDF）
            if hasattr(export_settings, 'export_sdf_mesh_type'):
                export_settings.export_sdf_mesh_type = 'dae'
                print(f"    ✓ 设置: export_sdf_mesh_type = 'dae'")
                success += 1
                
        except Exception as e:
            print(f"  phobosexportsettings mesh设置失败: {e}")
        
        # 设置Scene的mesh导出属性
        mesh_settings = {
            'export_mesh_dae': True,           # 启用DAE网格导出
            'export_mesh_stl': False,          # 禁用STL
            'export_mesh_obj': False,          # 禁用OBJ
        }
        
        for attr_name, value in mesh_settings.items():
            try:
                if hasattr(scene, attr_name):
                    setattr(scene, attr_name, value)
                    status = "启用" if value else "禁用"
                    print(f"    {status}: {attr_name}")
                    success += 1
                    
            except Exception as e:
                print(f"    设置 {attr_name} 失败: {e}")
        
        return success

class URDF_OT_PhobosCreateLink(Operator):
    """Create a Phobos Link"""
    bl_idname = "urdf.phobos_create_link"
    bl_label = "Create Phobos Link"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        try:
            # Ensure Phobos plugin is loaded
            if "phobos" not in bpy.context.preferences.addons:
                self.report({'ERROR'}, "Phobos插件未启用，请先安装并启用Phobos插件")
                return {'CANCELLED'}
            
            # Calling Phobos to create a link
            bpy.ops.phobos.create_links()
            
            self.report({'INFO'}, "Successfully created Phobos link")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Failed to create Phobos link: {str(e)}")
            return {'CANCELLED'}

class URDF_OT_SetJointRevolute(Operator):
    """Set Joint as Revolute Type"""
    bl_idname = "urdf.set_joint_revolute"
    bl_label = "创建转动关节"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        active_obj = context.active_object
        if not active_obj:
            self.report({'WARNING'}, "No active object selected")
            return {'CANCELLED'}
        
        try:
            # 设置 Phobos 对象类型
            self.setup_phobos_link(active_obj)
            
            # 设置旋转关节属性
            self.setup_revolute_joint(active_obj)
            
            # 应用 Phobos 约束
            self.apply_phobos_constraints(active_obj)
            
            self.report({'INFO'}, f"Object '{active_obj.name}' set as Revolute Joint")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to set revolute joint: {str(e)}")
            print(f"Revolute joint error: {e}")
            return {'CANCELLED'}
    
    def setup_phobos_link(self, obj):
        """设置 Phobos link 类型"""
        try:
            # 使用 Phobos 操作符设置类型
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            
            if hasattr(bpy.ops.phobos, 'set_phobostype'):
                bpy.ops.phobos.set_phobostype(phobostype='link')
                print("Set phobostype using Phobos operator")
            else:
                # 手动设置
                if 'phobostype' in obj and isinstance(obj.get('phobostype'), int):
                    del obj['phobostype']
                obj['phobostype'] = 'link'
                print("Manually set phobostype to 'link'")
                
        except Exception as e:
            print(f"Setup phobos link failed: {e}")
    
    def setup_revolute_joint(self, obj):
        """设置旋转关节属性"""
        try:
            # 清除旧的关节属性
            keys_to_remove = [key for key in obj.keys() if key.startswith('joint/')]
            for key in keys_to_remove:
                del obj[key]
            
            # 设置旋转关节属性
            obj['joint/type'] = 'revolute'
            obj['joint/name'] = obj.name + "_joint"
            obj['joint/axis'] = [0.0, 0.0, 1.0]  # Z轴旋转
            obj['joint/limits/lower'] = -3.14159  # -π
            obj['joint/limits/upper'] = 3.14159   # π
            obj['joint/limits/effort'] = 1000.0   # 转矩 (N·m)
            obj['joint/limits/velocity'] = 1.0    # 角速度 (rad/s)
            
            print("Set revolute joint properties")
            
        except Exception as e:
            print(f"Setup revolute joint failed: {e}")
            raise e
    
    def apply_phobos_constraints(self, obj):
        """应用 Phobos 约束"""
        try:
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            
            # 调用 Phobos 约束定义
            if hasattr(bpy.ops.phobos, 'define_joint_constraints'):
                bpy.ops.phobos.define_joint_constraints()
                print("Applied Phobos joint constraints")
            
            # 设置对象显示
            if obj.type == 'EMPTY':
                obj.empty_display_type = 'ARROWS'
                obj.empty_display_size = 0.1
            
            # 更新场景
            bpy.context.view_layer.update()
            
        except Exception as e:
            print(f"Apply constraints failed: {e}")

class URDF_OT_SetJointPrismatic(Operator):
    """彻底设置Prismatic关节 - 简化版本"""
    bl_idname = "urdf.set_joint_prismatic"
    bl_label = "创建滑动关节"
    bl_description = "设置prismatic关节类型"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def execute(self, context):
        active_obj = context.active_object
        
        if active_obj is None:
            self.report({'ERROR'}, "请先选择一个对象")
            return {'CANCELLED'}
        
        try:
            # 确保对象被选中
            bpy.context.view_layer.objects.active = active_obj
            active_obj.select_set(True)
            
            # 第一步：预设所有prismatic属性
            self.report({'INFO'}, "步骤1: 预设prismatic属性...")
            
            # 预设关节类型为prismatic
            active_obj["joint/type"] = "prismatic"
            
            # 设置默认Z轴向
            active_obj["joint/axis"] = [0, 0, 1]
            
            # 设置prismatic关节限制
            active_obj["joint/limit/lower"] = -1.0
            active_obj["joint/limit/upper"] = 1.0
            active_obj["joint/limit/effort"] = 1000.0
            active_obj["joint/limit/velocity"] = 1.0
            active_obj["joint/dynamics/damping"] = 0.1
            active_obj["joint/dynamics/friction"] = 0.0
            
            # 第二步：调用Phobos操作
            self.report({'INFO'}, "步骤2: 调用Phobos操作...")
            
            try:
                if hasattr(bpy.ops.phobos, 'set_phobostype'):
                    bpy.ops.phobos.set_phobostype(phobostype='link')
                    self.report({'INFO'}, "已设置为link类型")
            except Exception as e:
                self.report({'WARNING'}, f"设置phobostype失败: {str(e)}")
            
            # 第三步：再次强制设置为prismatic（关键步骤）
            self.report({'INFO'}, "步骤3: 强制覆盖为prismatic...")
            
            # 多次设置确保生效
            for i in range(3):  # 重复3次确保设置生效
                active_obj["joint/type"] = "prismatic"
                active_obj["joint/axis"] = [0, 0, 1]  # Z轴
            
            # 第四步：调用Phobos的关节约束定义
            try:
                if hasattr(bpy.ops.phobos, 'define_joint_constraints'):
                    bpy.ops.phobos.define_joint_constraints()
                    self.report({'INFO'}, "已调用Phobos关节约束定义")
            except Exception as e:
                self.report({'WARNING'}, f"Phobos关节约束定义失败: {str(e)}")
            
            # 第五步：最终验证和强制设置
            self.report({'INFO'}, "步骤4: 最终验证和强制设置...")
            
            # 再次强制设置（在Phobos操作之后）
            active_obj["joint/type"] = "prismatic"
            
            # 确认设置成功
            final_type = active_obj.get("joint/type")
            if final_type == "prismatic":
                self.report({'INFO'}, f"✓ 成功！'{active_obj.name}' 已设置为Prismatic关节 (Z轴)")
            else:
                self.report({'ERROR'}, f"✗ 失败！最终类型为: {final_type}")
                # 尝试删除所有关节属性后重新设置
                joint_props = [key for key in active_obj.keys() if key.startswith("joint/")]
                for prop in joint_props:
                    del active_obj[prop]
                
                # 重新设置为prismatic
                active_obj["joint/type"] = "prismatic"
                active_obj["joint/axis"] = [0, 0, 1]
                active_obj["joint/limit/lower"] = -1.0
                active_obj["joint/limit/upper"] = 1.0
                active_obj["joint/limit/effort"] = 1000.0
                active_obj["joint/limit/velocity"] = 1.0
                
                self.report({'INFO'}, f"已重置并强制设置为Prismatic")
            
        except Exception as e:
            self.report({'ERROR'}, f"设置失败: {str(e)}")
            return {'CANCELLED'}
            
        return {'FINISHED'}

class URDF_OT_PhobosDefineJoint(Operator):
    """Define Joint Parameters (Phobos)"""
    bl_idname = "urdf.define_joint_phobos"
    bl_label = "Define Joint (Phobos)"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 限制参数
    limit_lower: bpy.props.FloatProperty(
        name="Lower Limit",
        default=-3.14159,
        description="Lower limit for joint movement"
    )
    
    limit_upper: bpy.props.FloatProperty(
        name="Upper Limit", 
        default=3.14159,
        description="Upper limit for joint movement"
    )
    
    def execute(self, context):
        active_obj = context.active_object
        if not active_obj:
            self.report({'WARNING'}, "No active object selected")
            return {'CANCELLED'}
        
        # 检查对象是否已经是关节
        if 'joint/type' not in active_obj:
            self.report({'WARNING'}, "Object is not a joint. Use 'Set Joint' buttons first.")
            return {'CANCELLED'}
        
        try:
            # 检查现有的limits属性路径并统一设置
            if 'joint/limits/lower' in active_obj or 'joint/limits/upper' in active_obj:
                # 使用 joint/limits/ 格式
                active_obj['joint/limits/lower'] = self.limit_lower
                active_obj['joint/limits/upper'] = self.limit_upper
                print(f"设置限制使用 joint/limits/ 格式")
            else:
                # 使用 joint/limit/ 格式（单数）
                active_obj['joint/limit/lower'] = self.limit_lower
                active_obj['joint/limit/upper'] = self.limit_upper
                print(f"设置限制使用 joint/limit/ 格式")
            
            # 强制 Phobos 更新
            self.force_phobos_update(active_obj)
            
            # 更新场景
            bpy.context.view_layer.update()
            
            joint_type = active_obj.get('joint/type', 'unknown')
            self.report({'INFO'}, f"Joint parameters updated ({joint_type})")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to update joint parameters: {str(e)}")
            print(f"详细错误: {e}")
            return {'CANCELLED'}
    
    def force_phobos_update(self, obj):
        """强制 Phobos 更新"""
        try:
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            
            # 调用 Phobos 更新操作符
            if hasattr(bpy.ops.phobos, 'batch_property'):
                bpy.ops.phobos.batch_property()
                print("Applied Phobos batch_property")
            
            # 强制对象更新
            obj.update_tag()
            bpy.context.view_layer.update()
            
        except Exception as e:
            print(f"Phobos update failed: {e}")
    
    def invoke(self, context, event):
        active_obj = context.active_object
        if not active_obj:
            self.report({'WARNING'}, "Please select an object first")
            return {'CANCELLED'}
        
        # 检查是否是关节对象
        if 'joint/type' not in active_obj:
            self.report({'WARNING'}, "Object is not a joint. Use 'Set Joint' buttons first.")
            return {'CANCELLED'}
        
        # 加载现有属性
        self.load_existing_properties(active_obj)
        
        return context.window_manager.invoke_props_dialog(self, width=350)
    
    def load_existing_properties(self, obj):
        """加载现有属性"""
        try:
            # 加载限制 - 检查两种可能的格式
            if 'joint/limits/lower' in obj:
                self.limit_lower = obj['joint/limits/lower']
            elif 'joint/limit/lower' in obj:
                self.limit_lower = obj['joint/limit/lower']
                
            if 'joint/limits/upper' in obj:
                self.limit_upper = obj['joint/limits/upper']
            elif 'joint/limit/upper' in obj:
                self.limit_upper = obj['joint/limit/upper']
            
            print(f"加载属性: 对象名称={obj.name}, 下限={self.limit_lower}, 上限={self.limit_upper}")
                
        except Exception as e:
            print(f"Could not load existing properties: {e}")
    
    def draw(self, context):
        layout = self.layout
        
        # 显示当前关节信息
        if context.active_object:
            box = layout.box()
            obj = context.active_object
            box.label(text=f"Object: {obj.name}", icon='OBJECT_DATA')
            
            joint_type = obj.get('joint/type', 'None')
            current_joint_name = obj.get('joint/name', 'Not set')
            
            if joint_type == 'revolute':
                box.label(text="Type: Revolute (Rotation)", icon='CON_ROTLIMIT')
                box.label(text="Units: Radians")
            elif joint_type == 'prismatic':
                box.label(text="Type: Prismatic (Linear)", icon='CON_LOCLIMIT')
                box.label(text="Units: Meters")
            else:
                box.label(text="Type: Not a joint", icon='ERROR')
            
            # 显示当前关节名称
            box.separator()
            col = box.column(align=True)
            col.scale_y = 0.8
            col.label(text=f"Current Joint Name: {current_joint_name}")
        
        layout.separator()
        
        # 一键命名按钮替换原来的name输入框
        layout.operator("urdf.auto_name_joint", text="自动命名Joint (linkn → Jointn)", icon='SORTALPHA')
        
        layout.separator()
        
        # 参数设置
        col = layout.column()
        col.prop(self, "limit_lower")
        col.prop(self, "limit_upper")
        
        # 提示信息
        layout.separator()
        info_box = layout.box()
        info_box.label(text="Auto Naming Info:", icon='INFO')
        col = info_box.column(align=True)
        col.scale_y = 0.8
        col.label(text="• Detects linkn format (link1, link2, etc.)")
        col.label(text="• Auto names as Jointn (Joint1, Joint2, etc.)")
        col.label(text="• Use 'Name Links' button first if needed")

class URDF_OT_AutoNameJoint(Operator):
    """一键自动命名关节 - 根据linkn格式自动生成Jointn名称"""
    bl_idname = "urdf.auto_name_joint"
    bl_label = "Auto Name Joint"
    bl_description = "自动根据linkn格式命名关节为Jointn"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def execute(self, context):
        active_obj = context.active_object
        
        if not active_obj:
            self.report({'ERROR'}, "请先选择一个对象")
            return {'CANCELLED'}
        
        # 检查对象是否已经是关节
        if 'joint/type' not in active_obj:
            self.report({'WARNING'}, "对象不是关节。请先使用 'Set Joint' 按钮。")
            return {'CANCELLED'}
        
        try:
            obj_name = active_obj.name
            
            # 检查是否符合linkn格式
            link_number = self.extract_link_number(obj_name)
            
            if link_number is None:
                # 不符合linkn格式，提供详细提示
                self.report({'WARNING'}, f"对象名称 '{obj_name}' 不符合linkn格式。请先使用 'Name Links' 按钮重命名为link1, link2, link3等格式。")
                return {'CANCELLED'}
            
            # 生成对应的Joint名称
            joint_name = f"Joint{link_number}"
            
            # 设置关节名称
            old_joint_name = active_obj.get('joint/name', 'None')
            active_obj['joint/name'] = joint_name
            
            # 强制更新
            bpy.context.view_layer.update()
            
            # 验证设置结果
            final_joint_name = active_obj.get('joint/name')
            
            if final_joint_name == joint_name:
                self.report({'INFO'}, f"✓ 成功！'{obj_name}' 的关节已命名为 '{joint_name}'")
                print(f"关节命名成功: {old_joint_name} → {joint_name}")
            else:
                self.report({'WARNING'}, f"命名可能失败: 期望 {joint_name}, 实际 {final_joint_name}")
                print(f"关节命名异常: 期望 {joint_name}, 实际 {final_joint_name}")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"自动命名失败: {str(e)}")
            print(f"自动命名错误详情: {e}")
            return {'CANCELLED'}
    
    def extract_link_number(self, name):
        """提取link名称中的数字，支持多种格式"""
        import re
        
        # 匹配 linkN 格式 (link1, link2, link3, etc.)
        patterns = [
            r'^link(\d+)$',           # 精确匹配 link1, link2, etc.
            r'^link(\d+)\..*$',       # 匹配 link1.001, link2.002, etc. (Blender重复名称)
            r'^.*link(\d+)$',         # 匹配末尾为linkN的情况
            r'^.*link(\d+)\..*$',     # 匹配包含linkN的复杂情况
        ]
        
        for pattern in patterns:
            match = re.match(pattern, name, re.IGNORECASE)
            if match:
                number = int(match.group(1))
                print(f"从名称 '{name}' 中提取到数字: {number}")
                return number
        
        # 如果都不匹配，返回None
        print(f"名称 '{name}' 不符合linkn格式")
        return None

class URDF_OT_DebugJointProperties(Operator):
    """调试关节属性 - 改进版本，显示所有关节数据"""
    bl_idname = "urdf.debug_joint_properties" 
    bl_label = "link属性检查（控制台输出）"
    bl_description = "显示当前对象的所有关节相关属性到控制台"
    bl_options = {'REGISTER'}
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def execute(self, context):
        active_obj = context.active_object
        
        if active_obj is None:
            self.report({'ERROR'}, "请先选择一个对象")
            return {'CANCELLED'}
        
        print(f"\n{'='*60}")
        print(f"DEBUG: 对象 '{active_obj.name}' 的关节属性分析")
        print(f"{'='*60}")
        
        # 显示所有自定义属性
        all_keys = list(active_obj.keys())
        print(f"所有自定义属性数量: {len(all_keys)}")
        
        if all_keys:
            print("所有自定义属性:")
            for key in sorted(all_keys):
                value = active_obj[key]
                print(f"  {key}: {value} (类型: {type(value).__name__})")
        else:
            print("  无自定义属性")
        
        print(f"\n{'-'*40}")
        
        # 专门显示关节属性
        joint_keys = [key for key in active_obj.keys() if key.startswith('joint/')]
        
        if joint_keys:
            print(f"关节属性数量: {len(joint_keys)}")
            print("关节属性详细信息:")
            for key in sorted(joint_keys):
                value = active_obj[key]
                print(f"  {key}: {value} (类型: {type(value).__name__})")
                
                # 特殊处理一些重要属性
                if key == "joint/type":
                    if value == "revolute":
                        print("    → 这是旋转关节 (Revolute)")
                    elif value == "prismatic":
                        print("    → 这是移动关节 (Prismatic) ✓")
                    else:
                        print(f"    → 未知关节类型: {value}")
                        
                elif key == "joint/axis":
                    if value == [1, 0, 0]:
                        print("    → X轴方向")
                    elif value == [0, 1, 0]:
                        print("    → Y轴方向")  
                    elif value == [0, 0, 1]:
                        print("    → Z轴方向")
                    else:
                        print(f"    → 自定义轴向: {value}")
                        
                elif key.startswith("joint/limit/"):
                    print(f"    → 限制参数: {value}")
        else:
            print("关节属性数量: 0")
            print("  ⚠ 未找到关节属性！此对象不是关节。")
        
        print(f"\n{'-'*40}")
        
        # 检查 phobostype
        if 'phobostype' in active_obj:
            phobos_type = active_obj['phobostype']
            print(f"Phobos类型: {phobos_type} (类型: {type(phobos_type).__name__})")
            
            if phobos_type == 'link':
                print("  → 这是Phobos Link对象 ✓")
            else:
                print(f"  → Phobos类型: {phobos_type}")
        else:
            print("Phobos类型: 未设置")
        
        # 检查对象基本信息
        print(f"\n对象基本信息:")
        print(f"  名称: {active_obj.name}")
        print(f"  类型: {active_obj.type}")
        print(f"  位置: {active_obj.location}")
        print(f"  旋转: {active_obj.rotation_euler}")
        
        print(f"\n{'='*60}")
        print("调试信息已输出到控制台")
        print(f"{'='*60}\n")
        
        # 同时在界面显示简要信息
        joint_props = {key: active_obj[key] for key in active_obj.keys() if key.startswith("joint/")}
        
        if not joint_props:
            self.report({'INFO'}, f"对象 '{active_obj.name}' 没有关节属性")
        else:
            joint_type = active_obj.get("joint/type", "未知")
            self.report({'INFO'}, f"对象 '{active_obj.name}' 关节类型: {joint_type} - 详细信息见控制台")
        
        return {'FINISHED'}

class URDF_PT_MainPanel(Panel):
    """Main panel for URDF tools"""
    bl_label = "URDF Data Processor"
    bl_idname = "URDF_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "URDF Tools"
    
    def draw(self, context):
        layout = self.layout
        
        # === 前置修改 ===
        box = layout.box()
        box.label(text="前置修改", icon='MODIFIER_DATA')
        col = box.column(align=True)
        col.operator("urdf.clear_parent_keep_transform", text="清除父类关系")
        col.operator("urdf.delete_non_mesh", text="删除多余模块（非网格类）")
        col.operator("urdf.set_visual_mesh", text="设定Phobos及几何类型")
        
        # === 快捷键 ===
        box = layout.box()
        box.label(text="快捷键", icon='KEYINGSET')
        col = box.column(align=True)
        col.operator("urdf.smart_join", text="组合物体")
        col.operator("urdf.create_link_at_selection", text="创建游标（选中点线面的几何中心）")
        col.operator("urdf.relevant_bones", text="相关骨骼")
        
        # === links创建及设定 ===
        box = layout.box()
        box.label(text="links创建及设定", icon='OUTLINER_OB_ARMATURE')
        col = box.column(align=True)
        col.operator("urdf.phobos_create_link", text="*创建link")
        col.operator("urdf.name_links", text="一键命名links（按数字）")
        col.operator("urdf.create_base_link", text="命名base_link")
        col.operator("urdf.parent_to_base", text="绑定非移动模块及其他link至base_link")
        col.operator("urdf.set_module_root", text="base_link设定")
        
        # === 关节设定 ===
        box = layout.box()
        box.label(text="关节设定", icon='CON_ROTLIMIT')
        col = box.column(align=True)
        col.operator("urdf.set_joint_revolute", text="创建转动关节")
        col.operator("urdf.set_joint_prismatic", text="创建滑动关节")
        col.operator("urdf.define_joint_phobos", text="*设定关节属性")
        col.operator("urdf.debug_joint_properties", text="link属性检查（控制台输出）")
        
        # === 导出设置 ===
        box = layout.box()
        box.label(text="导出设置", icon='EXPORT')
        col = box.column(align=True)
        col.operator("urdf.set_export_settings", text="设定模块及URDF类型")
        col.operator("urdf.select_export_path_and_export", text="选择路径并导出URDF")
        
        # === 当前对象信息 ===
        if context.active_object:
            box = layout.box()
            box.label(text="当前对象信息", icon='INFO')
            
            obj = context.active_object
            row = box.row()
            row.label(text=f"Name: {obj.name}")
            
            # 显示关节信息（如果有）
            if "joint/type" in obj:
                joint_type = obj.get('joint/type', 'N/A')
                
                # 显示关节类型
                if joint_type == "revolute":
                    row = box.row()
                    row.label(text="Type: Revolute (Rotation)", icon='CON_ROTLIMIT')
                elif joint_type == "prismatic":
                    row = box.row()
                    row.label(text="Type: Prismatic (Linear)", icon='CON_LOCLIMIT')
                else:
                    row = box.row()
                    row.label(text=f"Type: {joint_type}", icon='QUESTION')
                
                # 显示限制信息
                lower = obj.get("joint/limit/lower", obj.get("joint/limits/lower", None))
                upper = obj.get("joint/limit/upper", obj.get("joint/limits/upper", None))
                
                if lower is not None and upper is not None:
                    row = box.row()
                    if joint_type == "revolute":
                        row.label(text=f"Range: {lower:.2f} to {upper:.2f} rad")
                    elif joint_type == "prismatic":
                        row.label(text=f"Range: {lower:.2f} to {upper:.2f} m")
                    else:
                        row.label(text=f"Range: {lower:.2f} to {upper:.2f}")
                else:
                    row = box.row()
                    row.label(text="Range: Not set", icon='ERROR')
                    
                # 显示关节名称
                joint_name = obj.get('joint/name', 'Not set')
                row = box.row()
                row.label(text=f"Joint Name: {joint_name}")
            else:
                row = box.row()
                row.label(text="Type: Not a joint", icon='OBJECT_DATA')


# Keymap保持不变
addon_keymaps = []

def register():
    # Register all classes
    bpy.utils.register_class(URDF_OT_ClearParentKeepTransform)
    bpy.utils.register_class(URDF_OT_DeleteNonMesh)
    bpy.utils.register_class(URDF_OT_SetVisualMesh)
    bpy.utils.register_class(URDF_OT_SmartJoin)
    bpy.utils.register_class(URDF_OT_CreateLinkAtSelection)
    bpy.utils.register_class(URDF_OT_NameLinks)
    bpy.utils.register_class(URDF_OT_CreateBaseLink)
    bpy.utils.register_class(URDF_OT_ParentToBase)
    bpy.utils.register_class(URDF_OT_SetModuleRoot)
    bpy.utils.register_class(URDF_OT_RelevantBones)
    bpy.utils.register_class(URDF_OT_SelectExportPathAndExport)
    bpy.utils.register_class(URDF_OT_SetExportSettings)
    bpy.utils.register_class(URDF_OT_PhobosCreateLink)
    bpy.utils.register_class(URDF_OT_SetJointRevolute)
    bpy.utils.register_class(URDF_OT_SetJointPrismatic)
    bpy.utils.register_class(URDF_OT_PhobosDefineJoint)
    bpy.utils.register_class(URDF_OT_AutoNameJoint)
    bpy.utils.register_class(URDF_OT_DebugJointProperties)
    bpy.utils.register_class(URDF_PT_MainPanel)

    
    # Add keymaps
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
        
        # Define shortcuts
        kmi = km.keymap_items.new(URDF_OT_ClearParentKeepTransform.bl_idname, 'P', 'PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))
        
        kmi = km.keymap_items.new(URDF_OT_DeleteNonMesh.bl_idname, 'X', 'PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))
        
        kmi = km.keymap_items.new(URDF_OT_SetVisualMesh.bl_idname, 'V', 'PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))
        
        kmi = km.keymap_items.new(URDF_OT_SmartJoin.bl_idname, 'J', 'PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))
        
        kmi = km.keymap_items.new(URDF_OT_CreateLinkAtSelection.bl_idname, 'L', 'PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))
        
        kmi = km.keymap_items.new(URDF_OT_RelevantBones.bl_idname, 'P', 'PRESS', ctrl=True)
        addon_keymaps.append((km, kmi))
        
        kmi = km.keymap_items.new(URDF_OT_CreateBaseLink.bl_idname, 'B', 'PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))

def unregister():
    # Unregister classes
    bpy.utils.unregister_class(URDF_OT_ClearParentKeepTransform)
    bpy.utils.unregister_class(URDF_OT_DeleteNonMesh)
    bpy.utils.unregister_class(URDF_OT_SetVisualMesh)
    bpy.utils.unregister_class(URDF_OT_SmartJoin)
    bpy.utils.unregister_class(URDF_OT_CreateLinkAtSelection)
    bpy.utils.unregister_class(URDF_OT_NameLinks)
    bpy.utils.unregister_class(URDF_OT_CreateBaseLink)
    bpy.utils.unregister_class(URDF_OT_ParentToBase)
    bpy.utils.unregister_class(URDF_OT_SetModuleRoot)
    bpy.utils.unregister_class(URDF_OT_RelevantBones)
    bpy.utils.unregister_class(URDF_OT_SelectExportPathAndExport)
    bpy.utils.unregister_class(URDF_OT_SetExportSettings)
    bpy.utils.unregister_class(URDF_OT_PhobosCreateLink)
    bpy.utils.unregister_class(URDF_OT_SetJointRevolute)
    bpy.utils.unregister_class(URDF_OT_SetJointPrismatic)
    bpy.utils.unregister_class(URDF_OT_PhobosDefineJoint)
    bpy.utils.unregister_class(URDF_OT_AutoNameJoint)
    bpy.utils.unregister_class(URDF_OT_DebugJointProperties)
    bpy.utils.unregister_class(URDF_PT_MainPanel)
    
    # Remove keymaps
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

if __name__ == "__main__":
    register()
